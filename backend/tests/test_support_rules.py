from datetime import UTC, datetime
from decimal import Decimal
import unittest

from app.calculations import (
    calculate_cancellation,
    calculate_failed_pickup_credit,
    classify_ticket_severity,
)
from app.reliability import ReliabilityService


class SupportRuleTests(unittest.TestCase):
    def test_northstar_agreement_waives_booked_cancellation_fee(self) -> None:
        result = calculate_cancellation(
            account_external_id="ACCT-001",
            order_external_id="ORD-1001",
            status="BOOKED",
            booked_at=datetime(2026, 8, 16, 3, 30, tzinfo=UTC),
            cancellation_requested_at=datetime(2026, 8, 16, 5, 30, tzinfo=UTC),
            pickup_actual_at=None,
        )
        self.assertIs(result["can_cancel"], True)
        self.assertEqual(result["fee_inr"], 0)
        self.assertIn("Northstar Agreement", result["rule"])

    def test_lumenworks_credit_uses_contract_threshold_and_amount(self) -> None:
        result = calculate_failed_pickup_credit(
            account_external_id="ACCT-002",
            order_external_id="ORD-2002",
            pickup_window_end=datetime(2026, 8, 16, 1, 0, tzinfo=UTC),
            pickup_actual_at=None,
            snapshot_at=datetime(2026, 8, 16, 5, 30, tzinfo=UTC),
            carrier_fault=True,
            customer_fault=False,
            shipment_fee_inr=Decimal("2400"),
        )
        self.assertIs(result["eligible"], True)
        self.assertEqual(result["credit_inr"], 300)
        self.assertEqual(result["threshold_hours"], 4)

    def test_delivered_order_is_not_treated_as_return_to_origin(self) -> None:
        result = calculate_cancellation(
            account_external_id="ACCT-004",
            order_external_id="ORD-4001",
            status="DELIVERED",
            booked_at=datetime(2026, 8, 15, 4, 0, tzinfo=UTC),
            cancellation_requested_at=None,
            pickup_actual_at=datetime(2026, 8, 15, 5, 0, tzinfo=UTC),
        )
        self.assertIs(result["can_cancel"], False)
        self.assertEqual(result["rule"], "SOP v4 - DELIVERED")

    def test_security_exposure_is_classified_as_p1(self) -> None:
        self.assertEqual(
            classify_ticket_severity("Possible production API key exposure", "Investigate"),
            "P1",
        )

    def test_credit_calculation_cannot_claim_automatic_execution(self) -> None:
        guarded = ReliabilityService.guard_action_claims(
            "Eligible for INR 300.\nNo further action is required; the credit will be applied automatically.",
            {"calculate_service_credit_outcome"},
        )
        self.assertNotIn("applied automatically", guarded)
        self.assertIn("has not issued or applied a credit", guarded)
