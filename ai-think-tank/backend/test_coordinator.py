import unittest
from unittest.mock import AsyncMock, patch

from graph.nodes.coordinator import coordinator_node
from models.expert import ExpertGroups, ExpertProfile


def build_expert(name: str, domain: str) -> ExpertProfile:
    # The test only needs stable shape, so the fields stay intentionally simple.
    return ExpertProfile(
        name=name,
        domain=domain,
        thinking_style="清晰、务实",
        focus=f"{domain} 视角",
        avatar_emoji="🧠",
        system_prompt=f"你是{name}。",
    )


class CoordinatorNodeTests(unittest.IsolatedAsyncioTestCase):
    async def test_coordinator_merges_three_domain_and_three_cross_experts(self):
        mocked_result = ExpertGroups(
            current_domain_experts=[
                build_expert("领域专家1", "核心领域"),
                build_expert("领域专家2", "核心领域"),
                build_expert("领域专家3", "核心领域"),
            ],
            cross_domain_experts=[
                build_expert("跨域专家1", "心理学"),
                build_expert("跨域专家2", "经济学"),
                build_expert("跨域专家3", "伦理学"),
            ],
        )

        with patch(
            "graph.nodes.coordinator.invoke_structured",
            new=AsyncMock(return_value=mocked_result),
        ):
            # This verifies the coordinator preserves the 3 + 3 expert ordering.
            result = await coordinator_node(
                {
                    "question": "AI 会如何影响教育？",
                    "experts": [],
                    "expert_responses": [],
                    "final_report": "",
                }
            )

        experts = result["experts"]

        self.assertEqual(len(experts), 6)
        self.assertEqual(
            [expert.name for expert in experts[:3]],
            ["领域专家1", "领域专家2", "领域专家3"],
        )
        self.assertEqual(
            [expert.name for expert in experts[3:]],
            ["跨域专家1", "跨域专家2", "跨域专家3"],
        )


if __name__ == "__main__":
    unittest.main()
