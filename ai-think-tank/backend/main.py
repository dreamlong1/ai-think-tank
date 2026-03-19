import json
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# 先加载环境变量配置，避免后续模块读取到空值
import config

from models.api import QuestionRequest
from graph.builder import graph_app
from services.structured_llm import StructuredLLMError

app = FastAPI(title="AI Think Tank API")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def event_generator(question: str):
    # 先发一条系统提示，让前端立刻进入“思考中”状态
    yield build_sse_event(
        "system_notice",
        {"message": "🤖 AI 智囊团正在为您召集专家..."},
    )
    
    # 初始化图运行所需的状态
    init_state = {"question": question, "experts": [], "expert_responses": [], "final_report": ""}
    
    try:
        # 逐步流式输出 LangGraph 运行过程中的事件
        async for event in graph_app.astream(init_state, stream_mode="updates"):
            # event 是一个字典，key 为刚执行完成的节点名
            for node_name, state_update in event.items():
                if node_name == "coordinator_node":
                    # 协调节点已经生成专家列表
                    experts = state_update.get("experts", [])
                    for expert in experts:
                        yield build_sse_event(
                            "expert_join",
                            {
                                "name": expert.name,
                                "domain": expert.domain,
                                "avatar_emoji": expert.avatar_emoji,
                            },
                        )
                        await asyncio.sleep(0.5)

                    yield build_sse_event(
                        "system_notice",
                        {"message": "专家已就位，开始讨论..."},
                    )
                    
                    # 告诉前端所有专家都处于“正在输入”状态
                    for expert in experts:
                        yield build_sse_event(
                            "expert_typing",
                            {
                                "name": expert.name,
                                "avatar_emoji": expert.avatar_emoji,
                            },
                        )

                elif node_name == "expert_node":
                    # 某位专家已经完成发言
                    responses = state_update.get("expert_responses", [])
                    for resp in responses:
                        yield build_sse_event(
                            "expert_message",
                            {
                                "name": resp.expert_name,
                                "avatar_emoji": resp.avatar_emoji,
                                "message": resp.message,
                                "key_points": resp.key_points,
                                "conclusion": resp.conclusion,
                                "confidence": resp.confidence,
                            },
                        )

                elif node_name == "synthesizer_node":
                    # `astream(..., stream_mode="updates")` 只会在节点执行完成后返回更新
                    # 所以这里拿到的是总结节点的最终结果，而不是“进行中”状态
                    final_report_json = state_update.get("final_report", "{}")
                    # 尝试解析为字典，失败时回退到兼容结构
                    try:
                        report_dict = json.loads(final_report_json)
                    except json.JSONDecodeError:
                        report_dict = {
                            "consensus": "N/A",
                            "disagreements": "N/A",
                            "blind_spots": "N/A",
                            "conclusion": final_report_json,
                        }
                    
                    yield build_sse_event("summary_message", report_dict)
    except StructuredLLMError as exc:
        logger.warning("Structured LLM execution failed: %s", exc.details or exc)
        # 结构化错误转成 SSE 事件，前端能展示可读提示而不是直接断流。
        yield build_sse_event(
            "analysis_error",
            {"code": exc.code, "message": exc.user_message},
        )
    except Exception:
        logger.exception("Unexpected graph streaming failure")
        yield build_sse_event(
            "analysis_error",
            {
                "code": "internal_error",
                "message": "分析过程中出现未预期错误，请稍后重试。",
            },
        )
    finally:
        # 不管中途成败，都发 done，避免前端一直停留在加载态。
        yield build_sse_event("done", {})


def build_sse_event(event_name: str, payload: dict) -> dict:
    return {
        "event": event_name,
        "data": json.dumps(payload, ensure_ascii=False),
    }

@app.post("/api/think")
async def think_endpoint(req: QuestionRequest):
    return EventSourceResponse(event_generator(req.question))

@app.get("/api/history")
async def history_endpoint():
    # 历史记录功能暂未接入数据库，目前返回空列表
    return {"history": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
