from __future__ import annotations


GENERAL_STATES = ["new", "reviewing", "approved", "needs-work", "deferred", "completed"]
SUBSTATES = [
    "unknown-doc-type",
    "needs-case-link",
    "needs-district-link",
    "needs-person-link",
    "needs-event-link",
    "ai-conflict",
    "parser-warning",
    "new-field-candidate",
    "new-doc-type-candidate",
    "awaiting-manual-date",
    "awaiting-privacy-review",
    "ready-for-publish",
]


def default_substates(doc_type_confidence: float, extract: dict, has_suggestions: bool) -> list[str]:
    states: list[str] = []
    if doc_type_confidence < 0.6:
        states.append("unknown-doc-type")
        states.append("new-doc-type-candidate")
    if not extract.get("caseHints"):
        states.append("needs-case-link")
    if not extract.get("districtHints"):
        states.append("needs-district-link")
    if extract.get("parseWarnings"):
        states.append("parser-warning")
    if not extract.get("documentDate"):
        states.append("awaiting-manual-date")
    if has_suggestions:
        states.append("ready-for-publish") if not states else None
    return sorted(set(states))


def can_transition(current: str, target: str) -> bool:
    allowed = {
        "new": {"reviewing", "deferred"},
        "reviewing": {"approved", "needs-work", "deferred", "completed"},
        "approved": {"completed", "reviewing"},
        "needs-work": {"reviewing", "deferred"},
        "deferred": {"reviewing"},
        "completed": {"reviewing"},
    }
    return target in allowed.get(current, set())
