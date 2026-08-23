from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any


def classify_ticket_severity(subject: str, description: str) -> str:
    text = f"{subject} {description}".lower()
    p1_markers = (
        "all shipment creation is failing",
        "every user",
        "production outage",
        "api key exposure",
        "credential exposure",
        "security incident",
    )
    if any(marker in text for marker in p1_markers):
        return "P1"
    p2_markers = (
        "bulk upload fails",
        "major feature",
        "materially degraded",
    )
    if any(marker in text for marker in p2_markers):
        return "P2"
    return "P3"


def calculate_cancellation(
    *,
    account_external_id: str,
    order_external_id: str,
    status: str,
    booked_at: datetime,
    cancellation_requested_at: datetime | None,
    pickup_actual_at: datetime | None,
) -> dict[str, Any]:
    status_upper = status.upper()
    if status_upper == "DRAFT":
        return {
            "order_id": order_external_id,
            "can_cancel": True,
            "fee_inr": 0,
            "outcome": "DRAFT shipments may be cancelled without a fee.",
            "rule": "SOP v4 - Order cancellation",
            "human_review_required": False,
        }
    if status_upper == "DELIVERED":
        return {
            "order_id": order_external_id,
            "can_cancel": False,
            "fee_inr": None,
            "outcome": "Delivered shipments cannot be cancelled.",
            "rule": "SOP v4 - DELIVERED",
            "human_review_required": False,
        }
    if status_upper == "PICKED_UP" or pickup_actual_at is not None:
        return {
            "order_id": order_external_id,
            "can_cancel": False,
            "fee_inr": None,
            "outcome": "The shipment has been picked up; use return-to-origin instead of cancellation.",
            "rule": "SOP v4 - PICKED_UP",
            "human_review_required": False,
        }
    if status_upper != "BOOKED":
        return {
            "order_id": order_external_id,
            "can_cancel": None,
            "fee_inr": None,
            "outcome": f"Cancellation rules for status {status_upper} are not supplied.",
            "rule": None,
            "human_review_required": True,
        }
    if cancellation_requested_at is None:
        return {
            "order_id": order_external_id,
            "can_cancel": True,
            "fee_inr": None,
            "outcome": "The shipment is BOOKED and not picked up, but no cancellation-request time is recorded.",
            "rule": "SOP v4 - BOOKED before pickup",
            "human_review_required": True,
        }

    minutes_after_booking = int((cancellation_requested_at - booked_at).total_seconds() // 60)
    northstar_waiver = account_external_id == "ACCT-001"
    fee = 0 if minutes_after_booking <= 30 or northstar_waiver else 250
    if northstar_waiver:
        rule = "Northstar Agreement section 2 overrides SOP v4 fee"
        outcome = "Northstar may cancel a BOOKED shipment before pickup with no cancellation fee."
    elif minutes_after_booking <= 30:
        rule = "SOP v4 - BOOKED within 30 minutes"
        outcome = "The BOOKED shipment may be cancelled without a fee within 30 minutes of booking."
    else:
        rule = "SOP v4 - BOOKED after 30 minutes"
        outcome = "The BOOKED shipment may be cancelled before pickup with an INR 250 fee."
    return {
        "order_id": order_external_id,
        "can_cancel": True,
        "fee_inr": fee,
        "minutes_after_booking": minutes_after_booking,
        "outcome": outcome,
        "rule": rule,
        "human_review_required": False,
    }


def calculate_failed_pickup_credit(
    *,
    account_external_id: str,
    order_external_id: str,
    pickup_window_end: datetime,
    pickup_actual_at: datetime | None,
    snapshot_at: datetime,
    carrier_fault: bool | None,
    customer_fault: bool | None,
    shipment_fee_inr: Decimal,
) -> dict[str, Any]:
    evaluation_time = pickup_actual_at or snapshot_at
    delay_hours = max(0.0, (evaluation_time - pickup_window_end).total_seconds() / 3600)
    base = {
        "order_id": order_external_id,
        "delay_hours": round(delay_hours, 2),
        "carrier_fault": carrier_fault,
        "customer_fault": customer_fault,
        "evaluated_at": evaluation_time.isoformat(),
    }
    if carrier_fault is None or customer_fault is None:
        return {
            **base,
            "eligible": None,
            "credit_inr": None,
            "outcome": "Fault attribution is incomplete; do not promise a service credit.",
            "rule": "SOP v4 - Approval and uncertainty",
            "human_review_required": True,
        }
    if not carrier_fault or customer_fault:
        return {
            **base,
            "eligible": False,
            "credit_inr": 0,
            "outcome": "The supplied fault conditions for a failed-pickup credit are not met.",
            "rule": "SOP v4 - Failed-pickup service credits",
            "human_review_required": False,
        }

    if account_external_id == "ACCT-002":
        eligible = delay_hours > 4
        return {
            **base,
            "eligible": eligible,
            "credit_inr": 300 if eligible else 0,
            "threshold_hours": 4,
            "outcome": (
                "LumenWorks is eligible for the fixed INR 300 credit."
                if eligible
                else "The delay does not exceed LumenWorks' four-hour contractual threshold."
            ),
            "rule": "LumenWorks Agreement section 3 overrides SOP v4",
            "human_review_required": False,
        }

    eligible = delay_hours > 2
    credit = min(Decimal("500"), shipment_fee_inr * Decimal("0.10")) if eligible else Decimal("0")
    return {
        **base,
        "eligible": eligible,
        "credit_inr": float(credit),
        "threshold_hours": 2,
        "outcome": (
            f"The default failed-pickup credit is INR {credit:.2f}."
            if eligible
            else "The delay does not exceed the default two-hour threshold."
        ),
        "rule": "SOP v4 - Failed-pickup service credits",
        "human_review_required": False,
        "note": "Northstar monthly aggregate credits are capped at INR 5,000." if account_external_id == "ACCT-001" else None,
    }


def evaluate_ticket_sla(
    *,
    account_external_id: str,
    plan: str,
    severity: str,
    created_at: datetime,
    snapshot_at: datetime,
) -> dict[str, Any]:
    target_minutes: int | None = None
    source = "Support Policy v3"
    coverage = "business_time"

    if account_external_id == "ACCT-001":
        source = "Northstar Agreement section 1"
        target_minutes = {"P1": 15, "P2": 60}.get(severity)
        coverage = "24x7" if severity == "P1" else "business_time"
    elif account_external_id == "ACCT-002":
        source = "LumenWorks Agreement section 1"
        target_minutes = None
        coverage = "business_time_no_weekends"
    elif plan == "Enterprise" and severity == "P1":
        target_minutes = 30
        coverage = "24x7"

    if target_minutes is None or coverage != "24x7":
        return {
            "severity": severity,
            "target": "business-time target",
            "coverage": coverage,
            "breached": None,
            "source": source,
            "outcome": "Exact breach time requires ParcelPilot's business-hours calendar, which is not supplied.",
            "human_review_required": True,
        }

    due_at = created_at + timedelta(minutes=target_minutes)
    breached = snapshot_at > due_at
    return {
        "severity": severity,
        "target_minutes": target_minutes,
        "coverage": coverage,
        "due_at": due_at.isoformat(),
        "breached": breached,
        "source": source,
        "outcome": "The first-response target is breached." if breached else "The first-response target is not yet breached.",
        "human_review_required": False,
    }
