from __future__ import annotations

from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
import re

from ..common import doc_id_for_hash, ensure_dir, person_entity_id, rel_path, sha256_bytes, slugify
from ..classify import classify_document
from .common import base_extract, guess_case_ids, guess_district_codes, iso_date_from_datetime


def parse_email(root: Path, doc: dict, path: Path) -> tuple[dict, dict, list[dict], list[dict], list[dict]]:
    extract = base_extract(doc, "email", doc.get("docType") or "email-correspondence")
    raw = path.read_bytes()
    message = BytesParser(policy=policy.default).parsebytes(raw)
    subject = str(message.get("subject") or "").strip()
    message_id = str(message.get("message-id") or "").strip()
    sent_dt = None
    try:
        sent_dt = parsedate_to_datetime(str(message.get("date") or "")) if message.get("date") else None
    except (TypeError, ValueError, IndexError):
        sent_dt = None

    sender_list = getaddresses(message.get_all("from", []))
    to_list = getaddresses(message.get_all("to", []))
    cc_list = getaddresses(message.get_all("cc", []))

    body_parts: list[str] = []
    attachments: list[dict] = []
    attachment_docs: list[dict] = []
    attachment_dir = root / "data" / "raw" / "email-attachments" / slugify(doc.get("id", "email"))
    for part in message.walk():
        filename = part.get_filename()
        ctype = part.get_content_type()
        if filename:
            raw_payload = part.get_payload(decode=True)
            payload = raw_payload if isinstance(raw_payload, bytes) else b""
            ext = Path(filename).suffix.lower()
            family, doc_type, confidence = classify_document(filename, ext, filename)
            attachment_sha = sha256_bytes(payload)
            child_doc_id = doc_id_for_hash(attachment_sha)
            ensure_dir(attachment_dir)
            safe_name = Path(filename).name or f"attachment{ext or '.bin'}"
            target = attachment_dir / safe_name
            if target.exists() and target.read_bytes() != payload:
                stem = target.stem
                suffix = target.suffix
                idx = 2
                while True:
                    candidate = attachment_dir / f"{stem}-{idx}{suffix}"
                    if not candidate.exists():
                        target = candidate
                        break
                    idx += 1
            if not target.exists():
                target.write_bytes(payload)
            rel_target = rel_path(target, root)
            attachments.append(
                {
                    "childDocId": child_doc_id,
                    "fileName": filename,
                    "mimeType": ctype,
                    "extension": ext,
                    "sizeBytes": len(payload),
                    "docFamily": family,
                    "docType": doc_type,
                    "docTypeConfidence": confidence,
                    "processSignals": _process_signals(filename),
                    "currentPath": rel_target,
                    "sha256": attachment_sha,
                }
            )
            attachment_docs.append(
                {
                    "id": child_doc_id,
                    "type": "document",
                    "schemaVersion": "1.0",
                    "sha256": attachment_sha,
                    "sourcePath": rel_target,
                    "currentPath": rel_target,
                    "canonicalPath": rel_target,
                    "originalFileName": Path(filename).name,
                    "extension": ext,
                    "mimeType": ctype,
                    "sizeBytes": len(payload),
                    "sourceKind": "email-attachment",
                    "parentDocumentId": doc.get("id"),
                    "visibility": "internal",
                    "publishEligible": False,
                    "docFamily": family,
                    "docType": doc_type,
                    "docTypeConfidence": confidence,
                    "messageId": message_id,
                    "threadKey": str(message.get("in-reply-to") or message_id or "").strip(),
                    "parserUsed": "email-attachment",
                    "parserVersion": "1.0",
                    "notes": "Extracted from EML attachment",
                    "sourceRefs": [
                        {"kind": "attachment-of", "path": doc.get("currentPath")},
                        {"kind": "attachment-file", "path": rel_target},
                    ],
                    "createdAt": doc.get("createdAt"),
                    "updatedAt": doc.get("updatedAt"),
                }
            )
            continue
        if ctype == "text/plain":
            try:
                body_parts.append(part.get_content().strip())
            except (LookupError, UnicodeError):
                continue

    body_text = "\n".join([part for part in body_parts if part])[:4000]
    hint_text = f"{subject}\n{body_text}"
    process_signals = sorted(set(_process_signals(hint_text)))
    extract.update(
        {
            "title": subject or extract.get("title"),
            "summary": (body_text[:280] + "...") if len(body_text) > 280 else body_text,
            "documentDate": iso_date_from_datetime(sent_dt) or extract.get("documentDate"),
            "datePrecision": "day" if iso_date_from_datetime(sent_dt) else extract.get("datePrecision"),
            "dateDerivedFrom": "email-header-date" if iso_date_from_datetime(sent_dt) else extract.get("dateDerivedFrom"),
            "subjectLine": subject,
            "sender": _person_block(sender_list[0]) if sender_list else None,
            "recipients": [_person_block(item) for item in to_list],
            "cc": [_person_block(item) for item in cc_list],
            "caseHints": sorted(set(extract.get("caseHints", []) + guess_case_ids(hint_text))),
            "districtHints": sorted(set(extract.get("districtHints", []) + guess_district_codes(hint_text))),
            "attachments": attachments,
            "structuredFields": {
                "messageId": message_id,
                "threadKey": str(message.get("in-reply-to") or message_id or "").strip(),
                "attachmentCount": len(attachments),
                "attachmentFamilies": sorted({str(item.get("docFamily")) for item in attachments if item.get("docFamily")}),
                "processSignals": process_signals,
            },
            "textSpans": [{"label": "body-preview", "text": body_text[:500]}] if body_text else [],
            "statusSignals": sorted(set(extract.get("statusSignals", []) + process_signals)),
            "confidence": 0.92,
            "needsReview": True,
        }
    )

    people = _collect_people(sender_list, to_list, cc_list, doc)
    person_lookup = {tuple((p.get("emails") or [""])[:1] + [p.get("displayName", "")]): p.get("id") for p in people}

    sender_id = None
    if sender_list:
        sender_key = (sender_list[0][1].strip().lower(), (sender_list[0][0] or sender_list[0][1] or "").strip())
        sender_id = person_lookup.get(sender_key)

    recipient_ids = []
    for item in to_list:
        recipient_ids.append(person_lookup.get((item[1].strip().lower(), (item[0] or item[1] or "").strip())))
    cc_ids = []
    for item in cc_list:
        cc_ids.append(person_lookup.get((item[1].strip().lower(), (item[0] or item[1] or "").strip())))

    message_entity = {
        "id": doc.get("messageEntityId"),
        "type": "message",
        "schemaVersion": "1.0",
        "messageId": message_id,
        "threadKey": str(message.get("in-reply-to") or message_id or "").strip(),
        "subject": subject,
        "sentAt": sent_dt.isoformat().replace("+00:00", "Z") if sent_dt else "",
        "datePrecision": "day" if sent_dt else "unknown",
        "senderPersonId": sender_id,
        "recipientPersonIds": [value for value in recipient_ids if value],
        "ccPersonIds": [value for value in cc_ids if value],
        "organizationIds": [],
        "documentId": doc.get("id"),
        "attachmentDocumentIds": [],
        "sourceRefs": [{"kind": "file", "path": doc.get("currentPath")}],
        "createdAt": doc.get("createdAt"),
        "updatedAt": doc.get("updatedAt"),
    }

    participant_edges = []
    if sender_id:
        participant_edges.append(
            {
                "linkId": f"link:{sender_id}:{message_entity['id']}:sent",
                "fromType": "person",
                "fromId": sender_id,
                "toType": "message",
                "toId": message_entity["id"],
                "relationType": "sent-message",
                "confidence": 0.98,
                "createdBy": "deterministic",
                "createdAt": doc.get("updatedAt"),
                "notes": "Email sender parsed from RFC822 headers",
            }
        )
    return (extract, message_entity, participant_edges, people, attachment_docs)


def _process_signals(text: str) -> list[str]:
    value = (text or "").lower()
    signals = []
    mapping = {
        "appeal": ["appeal", "950 cmr 32.08"],
        "request-filed": ["public records request", "foia request", "ferpa request", "formal request"],
        "response-sent": ["response", "response letter", "district response", "rao response"],
        "fee-waiver": ["fee waiver", "affidavit of indigency", "excessive fees"],
        "additional-information": ["additional information", "supplemental", "clarification"],
        "withdrawal": ["withdrawal", "voluntary withdrawal"],
        "follow-up": ["follow-up", "follow up", "reminder"],
        "settlement": ["settlement offer", "settlement"],
    }
    for signal, tokens in mapping.items():
        if any(token in value for token in tokens):
            signals.append(signal)
    if re.search(r"\bspr\d{2}[._-]\d{4}\b", text or "", flags=re.IGNORECASE):
        signals.append("spr-process")
    return sorted(set(signals))


def _person_block(value: tuple[str, str]) -> dict:
    return {
        "name": (value[0] or value[1] or "").strip(),
        "email": (value[1] or "").strip().lower(),
        "role": "",
        "organization": None,
    }


def _collect_people(sender_list: list[tuple[str, str]], to_list: list[tuple[str, str]], cc_list: list[tuple[str, str]], doc: dict) -> list[dict]:
    people = []
    ordered = sender_list[:1] + to_list + cc_list
    seen = set()
    for name, email in ordered:
        token = (email or name).strip().lower()
        if not token or token in seen:
            continue
        seen.add(token)
        people.append(
            {
                "id": person_entity_id((name or email or "").strip(), email.strip().lower()),
                "type": "person",
                "schemaVersion": "1.0",
                "displayName": (name or email or "Unknown").strip(),
                "givenName": "",
                "familyName": "",
                "emails": [email.strip().lower()] if email else [],
                "phones": [],
                "roles": [],
                "organizationIds": [],
                "aliases": [],
                "notes": "",
                "sourceRefs": [{"kind": "document", "path": doc.get("currentPath")}],
                "createdAt": doc.get("createdAt"),
                "updatedAt": doc.get("updatedAt"),
            }
        )
    return people
