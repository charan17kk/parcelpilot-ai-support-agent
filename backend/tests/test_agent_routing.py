import unittest

from app.agent.runner import AgentRunner
from app.reliability import ReliabilityService


class AgentRoutingTests(unittest.TestCase):
    def test_cancellation_question_routes_directly_to_calculator(self) -> None:
        self.assertEqual(
            AgentRunner.preferred_tool_call(
                "Can Northstar cancel ORD-1001 without a cancellation fee?"
            ),
            ("calculate_cancellation_outcome", {"order_id": "ORD-1001"}),
        )

    def test_ticket_question_routes_directly_to_ticket_lookup(self) -> None:
        self.assertEqual(
            AgentRunner.preferred_tool_call("Investigate TKT-501 and tell me its SLA."),
            ("lookup_ticket", {"ticket_id": "TKT-501"}),
        )

    def test_empty_model_answer_has_grounded_calculation_fallback(self) -> None:
        answer = ReliabilityService.fallback_answer(
            [
                {
                    "order_id": "ORD-1001",
                    "can_cancel": True,
                    "fee_inr": 0,
                    "outcome": "Northstar may cancel before pickup without a fee.",
                    "rule": "Northstar Agreement section 2",
                    "human_review_required": False,
                }
            ],
            [{"label": "[Order ORD-1001]"}],
        )
        self.assertIn("Cancellation allowed:** Yes", answer)
        self.assertIn("INR 0", answer)
        self.assertIn("[Order ORD-1001]", answer)


if __name__ == "__main__":
    unittest.main()
