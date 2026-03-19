from typing import TypedDict
from models.expert import ExpertResponse, ExpertProfile
from services.structured_llm import invoke_structured

EXPERT_DISCUSSION_PROMPT = (
    "你正在一个群聊讨论中发言。请基于你的专业角色身份，对以下问题给出你的分析和观点。\n"
    "要求：\n"
    "1. 用对话式的、自然的语气表达（像在群里发言，而不是写论文）\n"
    "2. 从你的专业角度深入分析，但表达要通俗易懂\n"
    "3. 提供具体的论据和案例\n"
    "4. 明确表达你的立场和结论"
)

class ExpertSubState(TypedDict):
    question: str
    expert_profile: dict  # 这里保留 dict，方便 `Send` API 传参和序列化

async def expert_node(state: ExpertSubState):
    profile_dict = state["expert_profile"]
    profile = ExpertProfile(**profile_dict) if isinstance(profile_dict, dict) else profile_dict

    result = await invoke_structured(
        system_prompt=f"{profile.system_prompt}\n\n{EXPERT_DISCUSSION_PROMPT}",
        user_prompt=state["question"],
        output_model=ExpertResponse,
    )
    
    result.expert_name = profile.name
    result.avatar_emoji = profile.avatar_emoji

    return {"expert_responses": [result]}
