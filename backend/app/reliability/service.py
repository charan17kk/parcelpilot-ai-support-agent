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
    def source_instruction() -> str:
        return (
            "Apply source precedence contextually: an active customer agreement controls applicable "
            "customer-specific terms; then current policy/SOP; then current product documentation. "
            "Deprecated policies and historical ticket resolutions are context only. If valid sources "
            "still conflict or a required fact is missing, say so and recommend escalation."
        )
