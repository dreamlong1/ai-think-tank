from pydantic import BaseModel, Field
from typing import List, Optional

class ExpertProfile(BaseModel):
    name: str = Field(description="角色名称，如'资深经济学家'")
    domain: str = Field(description="专业领域")
    thinking_style: str = Field(description="思维风格描述")
    focus: str = Field(description="该角色关注问题的哪个维度")
    avatar_emoji: str = Field(description="一个最能代表该角色的 Emoji 表情，用作群聊头像")
    system_prompt: str = Field(description="完整的角色设定提示词，用第二人称'你'来描述")

class ExpertProfiles(BaseModel):
    experts: List[ExpertProfile]


class ExpertGroups(BaseModel):
    # Experts directly tied to the user's current problem domain.
    current_domain_experts: List[ExpertProfile] = Field(
        min_length=3,
        max_length=3,
        description="与当前问题直接相关的 3 位当前领域专家",
    )
    # Experts from other domains used to broaden the discussion.
    cross_domain_experts: List[ExpertProfile] = Field(
        min_length=3,
        max_length=3,
        description="从其他领域引入的 3 位跨领域专家",
    )

class ExpertResponse(BaseModel):
    expert_name: str
    avatar_emoji: str
    message: str = Field(description="群聊中的发言内容，用自然的对话语气，篇幅适中")
    key_points: List[str] = Field(description="几个核心观点，最多3个")
    conclusion: str = Field(description="一句话核心结论")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)
