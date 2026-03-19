from models.expert import ExpertGroups, ExpertProfile
from graph.state import ThinkTankState
from services.structured_llm import invoke_structured

COORDINATOR_SYSTEM_PROMPT = (
    "你是一位跨学科研究顾问。用户将向你提出一个问题，你需要先识别问题的当前核心领域，"
    "再围绕这个领域组织一个 6 人专家组。\n"
    "要求：\n"
    "1. 必须生成 3 位当前领域专家，他们要直接处理问题所在的核心领域\n"
    "2. 必须生成 3 位跨领域专家，他们要来自不同学科，用外部视角补充判断\n"
    "3. 当前领域专家和跨领域专家都要避免角色重复\n"
    "4. 角色之间应有'张力'，观点可以互补，也可以冲突\n"
    "5. 为每位专家提供：角色名称、专业领域、思维风格、关注的核心维度\n"
    "6. 为每位专家补全一个适合群聊头像的 avatar_emoji\n"
    "7. 为每位专家补全完整的 system_prompt，用第二人称'你'来描述"
)

async def coordinator_node(state: ThinkTankState):
    result = await invoke_structured(
        system_prompt=COORDINATOR_SYSTEM_PROMPT,
        user_prompt=f"问题：{state['question']}",
        output_model=ExpertGroups,
    )

    # Keep the downstream graph unchanged by flattening both expert groups here.
    experts = _merge_expert_groups(result)
    return {"experts": experts}


def _merge_expert_groups(result: ExpertGroups) -> list[ExpertProfile]:
    return result.current_domain_experts + result.cross_domain_experts
