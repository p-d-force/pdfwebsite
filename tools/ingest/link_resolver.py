from __future__ import annotations

from .common import case_entity_id, org_entity_id, person_entity_id, utc_now


def build_doc_links(doc: dict, extract: dict) -> list[dict]:
    now = utc_now()
    links: list[dict] = []
    for case_id in extract.get("caseHints", []):
        links.append(
            {
                "linkId": f"link:{doc.get('id')}:{case_id}:belongs-to",
                "fromType": "document",
                "fromId": doc.get("id"),
                "toType": "case",
                "toId": case_entity_id(case_id),
                "relationType": "belongs-to",
                "confidence": 0.85,
                "createdBy": "deterministic",
                "createdAt": now,
                "notes": "Linked from parser case hints",
            }
        )
    for district_code in extract.get("districtHints", []):
        links.append(
            {
                "linkId": f"link:{doc.get('id')}:{district_code}:district",
                "fromType": "document",
                "fromId": doc.get("id"),
                "toType": "organization",
                "toId": org_entity_id(district_code),
                "relationType": "mentions-organization",
                "confidence": 0.8,
                "createdBy": "deterministic",
                "createdAt": now,
                "notes": "Linked from parser district hints",
            }
        )
    sender = extract.get("sender") or {}
    if sender.get("name") or sender.get("email"):
        pid = person_entity_id(sender.get("name", ""), sender.get("email", ""))
        links.append(
            {
                "linkId": f"link:{doc.get('id')}:{pid}:sender",
                "fromType": "document",
                "fromId": doc.get("id"),
                "toType": "person",
                "toId": pid,
                "relationType": "mentions-person",
                "confidence": 0.78,
                "createdBy": "deterministic",
                "createdAt": now,
                "notes": "Parsed email sender",
            }
        )
    return links
