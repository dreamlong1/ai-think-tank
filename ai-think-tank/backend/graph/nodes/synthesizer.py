from models.api import SummaryResponse
from graph.state import ThinkTankState
from services.structured_llm import invoke_structured

SYNTHESIZER_SYSTEM_PROMPT = (
    "你是一位高级分析师，负责综合多位专家对同一问题的独立分析。\n"
    "你的输出将作为群聊中的一条'总结卡片'展示。\n"
    "请完成以下任务：\n"
    "1. 【共识提炼】找出专家们观点的共同之处\n"
    "2. 【分歧分析】指出观点冲突的地方，分析冲突的原因\n"
    "3. 【盲点发现】指出所有专家可能都忽略的角度\n"
    "4. 【综合结论】给出你的综合性结论和建议"
)

async def synthesizer_node(state: ThinkTankState):
    responses_text = ""
    for r in state["expert_responses"]:
        responses_text += f"专家：{r.expert_name}\n结论：{r.conclusion}\n论点：{', '.join(r.key_points)}\n完整回答：{r.message}\n\n"

    result = await invoke_structured(
        system_prompt=SYNTHESIZER_SYSTEM_PROMPT,
        user_prompt=f"原始问题：{state['question']}\n\n各专家观点：\n{responses_text}",
        output_model=SummaryResponse,
    )
    
    return {"final_report": result.model_dump_json()}
