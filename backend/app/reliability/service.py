from typing import Any


class ReliabilityService:
    AUTHORITY_LABELS = {
        "customer_agreement": "Customer agreement - highest for applicable customer-specific terms",
        "current_policy": "Current policy",
        "current_sop": "Current operating procedure",
        "product_guide": "Current product documentation",
        "deprecated_policy": "Deprecated - historical reference only",
        "historical_ticket": "Historical context - not policy authority",
        "structured_record": "Structured operational record",
    }

    @classmethod
    def label(cls, authority_class: str) -> str:
        return cls.AUTHORITY_LABELS.get(authority_class, authority_class.replace("_", " ").title())

    @staticmethod
    def confidence(tool_results: list[dict[str, Any]], citations: list[dict[str, Any]]) -> str:
        if not tool_results and not citations:
            return "low"
        if any(result.get("human_review_required") for result in tool_results):
            return "low"
        if any(result.get("error") or result.get("not_found") for result in tool_results):
            return "low"
        classes = {citation.get("reliability_class") for citation in citations}
        if "deprecated_policy" in classes and not classes.intersection(
            {"customer_agreement", "current_policy", "current_sop"}
        ):
            return "low"
        has_structured = "structured_record" in classes
        has_authoritative = bool(
            classes.intersection({"customer_agreement", "current_policy", "current_sop", "product_guide"})
        )
        if has_structured and has_authoritative:
            return "high"
        if has_authoritative:
            return "medium"
        return "low"

    @staticmethod
    def guard_action_claims(content: str, tool_names: set[str]) -> str:
        """Prevent advisory calculations from being presented as executed mutations."""
        unsafe_phrases = (
            "applied automatically",
            "automatically applied",
            "has been applied",
            "will be applied",
            "credit has been issued",
            "credit was issued",
            "no further action is required",
        )
        paragraphs = content.splitlines()
        filtered = [
            line for line in paragraphs if not any(phrase in line.lower() for phrase in unsafe_phrases)
        ]
        guarded = "\n".join(filtered).rstrip()

        if "calculate_service_credit_outcome" in tool_names:
            guarded += (
                "\n\n**Action status:** This is an eligibility calculation only. "
                "ParcelPilot Assist has not issued or applied a credit."
            )
        if "calculate_cancellation_outcome" in tool_names:
            guarded += (
                "\n\n**Action status:** This is an eligibility and fee determination only. "
                "ParcelPilot Assist has not submitted a cancellation."
            )
        return guarded

    @staticmethod
    def fallback_answer(
        tool_results: list[dict[str, Any]], citations: list[dict[str, Any]]
    ) -> str:
        """Render a grounded response if a provider returns an empty final message."""

        if not tool_results:
            return (
                "I could not produce a grounded answer from the available data. "
                "Please retry or ask ParcelPilot support to review the request."
            )
        result = tool_results[-1]
        if result.get("not_found"):
            return "I could not find that record within your authorized account data."

        lines: list[str] = []
        order_id = result.get("order_id")
        ticket_id = result.get("ticket_id")
        if order_id:
            lines.append(f"**Verified outcome for {order_id}**")
        elif ticket_id:
            lines.append(f"**Verified ticket details for {ticket_id}**")

        if result.get("outcome"):
            lines.append(str(result["outcome"]))
        if "can_cancel" in result:
            allowed = result.get("can_cancel")
            lines.append(
                f"- **Cancellation allowed:** "
                f"{'Yes' if allowed is True else 'No' if allowed is False else 'Needs human review'}"
            )
            fee = result.get("fee_inr")
            lines.append(f"- **Cancellation fee:** {'Not applicable' if fee is None else f'INR {fee}'}")
        if "eligible" in result:
            eligible = result.get("eligible")
            lines.append(
                f"- **Service-credit eligible:** "
                f"{'Yes' if eligible is True else 'No' if eligible is False else 'Needs human review'}"
            )
            credit = result.get("credit_inr")
            lines.append(f"- **Credit amount:** {'Not determined' if credit is None else f'INR {credit}'}")
        if result.get("rule"):
            lines.append(f"- **Applicable rule:** {result['rule']}")
        if result.get("status"):
            lines.append(f"- **Status:** {result['status']}")
        if result.get("severity"):
            lines.append(f"- **Severity:** {result['severity']}")
        sla = result.get("sla")
        if isinstance(sla, dict) and sla.get("outcome"):
            lines.append(f"- **SLA:** {sla['outcome']}")
        if result.get("human_review_required"):
            lines.append("- **Human review:** Required because the supplied facts are incomplete or uncertain.")

        labels = [str(item.get("label")) for item in citations if item.get("label")]
        if labels:
            lines.append("\n**Sources:** " + ", ".join(labels))
        return "\n".join(lines).strip()

    @staticmethod
    def source_instruction() -> str:
        return (
            "Apply source precedence contextually: an active customer agreement controls applicable "
            "customer-specific terms; then current policy/SOP; then current product documentation. "
            "Deprecated policies and historical ticket resolutions are context only. If valid sources "
            "still conflict or a required fact is missing, say so and recommend escalation."
        )
