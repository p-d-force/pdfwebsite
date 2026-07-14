from __future__ import annotations

from .common import SCHEMA_VERSION, task_entity_id, utc_now
from .state_machine import default_substates


def build_review_task(doc: dict, extract: dict, suggestions: dict | None) -> dict:
    now = utc_now()
    return {
        "id": task_entity_id(doc.get("id", "doc:unknown")),
        "type": "review_task",
        "schemaVersion": SCHEMA_VERSION,
        "docId": doc.get("id"),
        "generalState": "new",
        "subStates": default_substates(float(doc.get("docTypeConfidence") or 0), extract, bool(suggestions)),
        "priority": "high" if extract.get("caseHints") else "medium",
        "assignedTo": None,
        "manualDocType": None,
        "manualCaseLinks": [],
        "manualDistrictLinks": [],
        "manualPeopleLinks": [],
        "manualEventLinks": [],
        "acceptedFields": [],
        "overrideFields": {},
        "rejectedSuggestions": [],
        "approvalHistory": [],
        "newFieldRequests": suggestions.get("suggestedNewFieldNames", []) if suggestions else [],
        "newDocTypeRequests": [suggestions.get("suggestedNewDocType")] if suggestions and suggestions.get("suggestedNewDocType") else [],
        "fileAction": "keep",
        "fileActionPayload": {},
        "reviewNotes": "",
        "reviewStartedAt": None,
        "reviewCompletedAt": None,
        "createdAt": now,
        "updatedAt": now,
    }


def build_queue_item(doc: dict, extract: dict, review_task: dict, suggestions: dict | None) -> dict:
    case_links = review_task.get("manualCaseLinks", []) or extract.get("caseHints", [])
    district_links = review_task.get("manualDistrictLinks", []) or extract.get("districtHints", [])
    return {
        "queueId": review_task.get("id"),
        "docId": doc.get("id"),
        "queueSource": doc.get("sourceKind"),
        "discoveredAt": doc.get("createdAt"),
        "currentLocation": doc.get("currentPath"),
        "generalState": review_task.get("generalState"),
        "subStates": review_task.get("subStates", []),
        "docFamily": doc.get("docFamily"),
        "docType": doc.get("docType"),
        "caseLinkCount": len(case_links),
        "districtLinkCount": len(district_links),
        "hasDeterministicExtract": True,
        "hasAiSuggestions": bool(suggestions),
        "hasConflicts": bool(suggestions and suggestions.get("conflictsWithDeterministic")),
        "hasUnknownFields": bool(suggestions and suggestions.get("suggestedNewFieldNames")),
        "priority": review_task.get("priority"),
        "lastTouchedAt": review_task.get("updatedAt"),
    }
