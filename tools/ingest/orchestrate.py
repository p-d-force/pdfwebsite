from __future__ import annotations

from pathlib import Path
from collections import Counter
import re

from ..common import read_json, slugify, sort_unique, write_json
from .classify import classify_document
from .common import (
    EDGE_ROOT,
    ENTITY_ROOT,
    INGEST_ROOT,
    SCHEMA_VERSION,
    append_jsonl,
    batch_entity_id,
    case_entity_id,
    doc_id_for_hash,
    ensure_ingest_dirs,
    load_case_metadata,
    message_entity_id,
    org_entity_id,
    person_entity_id,
    rel_path,
    sha256_file,
    utc_now,
    write_entity,
)
from .link_resolver import build_doc_links
from .parsers.attachment import parse_attachment
from .parsers.correspondence import parse_correspondence
from .parsers.determination import parse_determination
from .parsers.email import parse_email
from .parsers.prs import parse_prs
from .parsers.public_records import parse_public_records
from .parsers.spreadsheet import parse_spreadsheet
from .qa import summarize_qa
from .rules import load_all_rules, match_doc_family_rules
from .review_queue import build_queue_item, build_review_task


def _field_provenance(value: object, doc: dict, method: str, source_text: str = "", confidence: float | None = None) -> list[dict]:
    if value in (None, "", [], {}):
        return []
    return [
        {
            "sourceUrlOrPath": doc.get("currentPath", ""),
            "sourceEntityId": doc.get("id", ""),
            "sourceText": source_text or str(value)[:240],
            "method": method,
            "confidence": confidence,
            "approvalHistory": [],
        }
    ]


def _with_field_tracking(extract: dict, doc: dict) -> dict:
    tracked_fields = ["title", "summary", "documentDate", "caseHints", "districtHints", "requestNumbers", "deadlines", "statusSignals"]
    field_provenance = {}
    field_history = {}
    field_snapshots = []
    for field in tracked_fields:
        value = extract.get(field)
        field_provenance[field] = _field_provenance(value, doc, doc.get("parserUsed") or doc.get("docFamily") or "deterministic")
        field_history[field] = []
    field_snapshots.append(
        {
            "capturedAt": utc_now(),
            "sourceEntityId": doc.get("id"),
            "values": {field: extract.get(field) for field in tracked_fields},
        }
    )
    extract["fieldProvenance"] = field_provenance
    extract["fieldHistory"] = field_history
    extract["fieldSnapshots"] = field_snapshots
    return extract


def build_case_entities(root: Path) -> list[dict]:
    records = []
    for payload in load_case_metadata(root):
        case_id = payload.get("caseId")
        if not case_id:
            continue
        entity = {
            "id": case_entity_id(case_id),
            "type": "case",
            "schemaVersion": SCHEMA_VERSION,
            "caseId": case_id,
            "districtCode": payload.get("district") or payload.get("districtCode") or "",
            "districtName": payload.get("districtName", ""),
            "jurisdiction": "US-MA",
            "caseType": payload.get("caseType", "case"),
            "title": payload.get("subject") or case_id,
            "subject": payload.get("subject", ""),
            "status": payload.get("status", "open"),
            "statusLabel": payload.get("statusLabel", "Open"),
            "statusReason": payload.get("statusReason", ""),
            "currentStage": payload.get("currentStage", ""),
            "filedDate": payload.get("filedDate", ""),
            "nextDeadline": payload.get("nextDeadline", ""),
            "nextDeadlineDescription": payload.get("nextDeadlineDescription", ""),
            "priority": payload.get("priority", "medium"),
            "visibility": "public",
            "manualOverrides": {"status": True, "timeline": True},
            "sourceRefs": [{"kind": "metadata", "path": payload.get("sourceMetadata", "")}],
            "createdAt": utc_now(),
            "updatedAt": utc_now(),
        }
        write_entity(root, "cases", entity["id"], entity)
        records.append(entity)
    return records


def build_org_entities(root: Path, case_entities: list[dict]) -> list[dict]:
    seen = {}
    for case in case_entities:
        code = case.get("districtCode") or "UNKNOWN"
        if code in seen:
            continue
        entity = {
            "id": org_entity_id(code),
            "type": "organization",
            "schemaVersion": SCHEMA_VERSION,
            "name": case.get("districtName") or code,
            "shortName": case.get("districtName") or code,
            "orgType": "district" if code not in {"DESE"} else "agency",
            "districtCode": code,
            "parentOrgId": None,
            "location": "",
            "website": None,
            "contacts": [],
            "tags": ["district" if code not in {"DESE"} else "agency"],
            "sourceRefs": [{"kind": "case-entity", "path": case.get("id")}],
            "createdAt": utc_now(),
            "updatedAt": utc_now(),
        }
        write_entity(root, "orgs", entity["id"], entity)
        seen[code] = entity
    return list(seen.values())


def discover_documents(root: Path) -> list[dict]:
    found: list[dict] = []
    scan_roots = [(root / "intake", "intake")]
    scan_roots.extend((path, "case-intake") for path in root.glob("cases/*/*/intake"))
    now = utc_now()
    for base_path, source_kind in scan_roots:
        if not base_path.exists():
            continue
        for path in sorted(base_path.rglob("*")):
            if not path.is_file():
                continue
            if "completed" in {part.lower() for part in path.parts}:
                continue
            sha256 = sha256_file(path)
            doc_id = doc_id_for_hash(sha256)
            file_name = path.name
            extension = path.suffix.lower()
            doc_family, doc_type, confidence = classify_document(file_name, extension, rel_path(path, root))
            person_ids = {}
            found.append(
                {
                    "id": doc_id,
                    "type": "document",
                    "schemaVersion": SCHEMA_VERSION,
                    "sha256": sha256,
                    "sourcePath": rel_path(path, root),
                    "currentPath": rel_path(path, root),
                    "canonicalPath": rel_path(path, root),
                    "originalFileName": file_name,
                    "extension": extension,
                    "mimeType": _mime_from_extension(extension),
                    "sizeBytes": path.stat().st_size,
                    "sourceKind": source_kind,
                    "parentDocumentId": None,
                    "visibility": "internal",
                    "publishEligible": False,
                    "docFamily": doc_family,
                    "docType": doc_type,
                    "docTypeConfidence": confidence,
                    "messageId": "",
                    "threadKey": "",
                    "parserUsed": "",
                    "parserVersion": "1.0",
                    "notes": "",
                    "sourceRefs": [{"kind": source_kind, "path": rel_path(path, root)}],
                    "createdAt": now,
                    "updatedAt": now,
                    "messageEntityId": message_entity_id("", rel_path(path, root)),
                    "senderPersonId": None,
                    "recipientPersonIds": [],
                    "personIds": person_ids,
                }
            )
    deduped = {doc["id"]: doc for doc in found}
    for doc in deduped.values():
        write_entity(root, "documents", doc["id"], {k: v for k, v in doc.items() if k not in {"messageEntityId", "senderPersonId", "recipientPersonIds", "personIds"}})
    return sorted(deduped.values(), key=lambda item: item.get("currentPath", ""))


def parse_documents(root: Path, documents: list[dict], rules_bundle: dict[str, list[dict]]) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    extracts: list[dict] = []
    people: dict[str, dict] = {}
    messages: list[dict] = []
    edges: list[dict] = []
    attachment_documents: list[dict] = []
    family_rules = rules_bundle.get("doc-families", [])
    for doc in documents:
        path = root / doc.get("currentPath", "")
        matched_rules = match_doc_family_rules(doc, family_rules)
        doc["matchedRuleIds"] = [rule.get("id") for rule in matched_rules]
        doc["matchedRuleSources"] = [rule.get("sourcePath") for rule in matched_rules]
        parser_name = doc.get("docFamily")
        extract: dict
        if doc.get("docFamily") == "email":
            sender_people = []
            try:
                extract, message_entity, participant_edges, parsed_people, child_attachments = parse_email(root, doc, path)
                messages.append(message_entity)
                edges.extend(participant_edges)
                sender_people = parsed_people
                attachment_documents.extend(child_attachments)
            except Exception as exc:  # pragma: no cover - defensive
                extract = {"docId": doc.get("id"), "docFamily": "email", "docType": doc.get("docType"), "parseWarnings": [str(exc)], "caseHints": [], "districtHints": []}
            for person in sender_people:
                if not person.get("id"):
                    pid = person_entity_id(person.get("displayName", ""), (person.get("emails") or [""])[0])
                    person["id"] = pid
                people[person["id"]] = person
        elif doc.get("docFamily") == "public-records":
            extract = parse_public_records(doc, path)
        elif doc.get("docFamily") == "prs":
            extract = parse_prs(doc, path)
        elif doc.get("docFamily") == "determination":
            extract = parse_determination(doc, path)
        elif doc.get("docFamily") == "correspondence":
            extract = parse_correspondence(doc, path)
        elif doc.get("docFamily") == "spreadsheet":
            extract = parse_spreadsheet(doc, path)
        else:
            extract = parse_attachment(doc, path)

        doc["parserUsed"] = parser_name
        extract.setdefault("structuredFields", {})
        extract["structuredFields"]["appliedRuleIds"] = doc.get("matchedRuleIds", [])
        extract["structuredFields"]["appliedRuleSources"] = doc.get("matchedRuleSources", [])
        extract = _with_field_tracking(extract, doc)
        extracts.append(extract)
        edges.extend(build_doc_links(doc, extract))

    from collections import defaultdict
    thread_map = defaultdict(list)
    for msg in messages:
        if msg.get("threadKey"):
            thread_map[msg["threadKey"]].append(msg)
    for msgs in thread_map.values():
        msgs.sort(key=lambda m: m.get("sentAt") or "")

    suggestions: list[dict] = []
    for doc, extract in zip(documents, extracts):
        thread_context = []
        if doc.get("docFamily") == "email":
            tk = extract.get("structuredFields", {}).get("threadKey")
            if tk and tk in thread_map:
                current_msg = next((m for m in thread_map[tk] if m.get("documentId") == doc.get("id")), None)
                if current_msg:
                    for m in thread_map[tk]:
                        if (m.get("sentAt") or "") < (current_msg.get("sentAt") or ""):
                            thread_context.append({
                                "docId": m.get("documentId"),
                                "sentAt": m.get("sentAt"),
                                "subject": m.get("subject")
                            })
        suggestions.append(build_suggestion(doc, extract, thread_context))

    return (extracts, suggestions, list(people.values()), messages + [], edges, attachment_documents)


def build_suggestion(doc: dict, extract: dict, thread_context: list[dict] | None = None) -> dict:
    thread_context = thread_context or []
    rationale = "Heuristic suggestion lane mirrors deterministic extract until external model integration is configured. Thread context is evaluated to prevent deterministic summaries."
    suggestion = {
        "docId": doc.get("id"),
        "model": "local-heuristic-assist",
        "modelVersion": "1.0",
        "generatedAt": utc_now(),
        "suggestedDocType": doc.get("docType"),
        "suggestedTitle": extract.get("title", ""),
        "suggestedSummary": extract.get("summary", ""),
        "suggestedCaseLinks": extract.get("caseHints", []),
        "suggestedDistrictLinks": extract.get("districtHints", []),
        "suggestedPeopleLinks": extract.get("peopleHints", []),
        "suggestedDeadlines": extract.get("deadlines", []),
        "suggestedFields": {},
        "suggestedNewFieldNames": ["requestedItems"] if doc.get("docFamily") == "unknown" else [],
        "suggestedNewDocType": doc.get("docType") if float(doc.get("docTypeConfidence") or 0) < 0.6 else None,
        "confidence": round(max(0.25, float(extract.get("confidence") or 0) - 0.12), 2),
        "rationale": rationale,
        "sourceSupport": [doc.get("currentPath")],
        "appliedRuleIds": doc.get("matchedRuleIds", []),
        "threadContext": thread_context,
        "conflictsWithDeterministic": False,
        "reviewStatus": "new",
    }
    suggestion["fieldProvenance"] = {
        "suggestedDocType": _field_provenance(suggestion.get("suggestedDocType"), doc, "heuristic-suggestion", str(suggestion.get("suggestedDocType", "")), suggestion.get("confidence")),
        "suggestedTitle": _field_provenance(suggestion.get("suggestedTitle"), doc, "heuristic-suggestion", str(suggestion.get("suggestedTitle", "")), suggestion.get("confidence")),
        "suggestedSummary": _field_provenance(suggestion.get("suggestedSummary"), doc, "heuristic-suggestion", str(suggestion.get("suggestedSummary", ""))[:240], suggestion.get("confidence")),
    }
    suggestion["fieldHistory"] = {"suggestedDocType": [], "suggestedTitle": [], "suggestedSummary": []}
    suggestion["fieldSnapshots"] = [
        {
            "capturedAt": suggestion.get("generatedAt"),
            "sourceEntityId": doc.get("id"),
            "values": {
                "suggestedDocType": suggestion.get("suggestedDocType"),
                "suggestedTitle": suggestion.get("suggestedTitle"),
                "suggestedSummary": suggestion.get("suggestedSummary"),
            },
        }
    ]
    return suggestion


def build_people_entities(root: Path, people: list[dict]) -> list[dict]:
    for person in people:
        write_entity(root, "people", person["id"], person)
    return people


def load_existing_review_tasks(root: Path) -> dict[str, dict]:
    task_dir = root / ENTITY_ROOT / "review_tasks"
    if not task_dir.exists():
        return {}
    records: dict[str, dict] = {}
    for path in sorted(task_dir.glob("*.json")):
        task = read_json(path, default={})
        doc_id = task.get("docId")
        if doc_id:
            records[doc_id] = task
    return records


def merge_review_task(existing: dict | None, fresh: dict) -> dict:
    if not existing:
        return fresh
    merged = dict(fresh)
    for key in [
        "generalState",
        "assignedTo",
        "manualDocType",
        "manualCaseLinks",
        "manualDistrictLinks",
        "manualPeopleLinks",
        "manualEventLinks",
        "acceptedFields",
        "overrideFields",
        "rejectedSuggestions",
        "approvalHistory",
        "fileAction",
        "fileActionPayload",
        "reviewNotes",
        "reviewStartedAt",
        "reviewCompletedAt",
        "createdAt",
    ]:
        if key in existing and existing.get(key) not in (None, "", [], {}):
            merged[key] = existing.get(key)
    merged["subStates"] = sorted(set(existing.get("subStates", []) + fresh.get("subStates", [])))
    merged["newFieldRequests"] = sorted(set(existing.get("newFieldRequests", []) + fresh.get("newFieldRequests", [])))
    merged["newDocTypeRequests"] = sorted(set(existing.get("newDocTypeRequests", []) + fresh.get("newDocTypeRequests", [])))
    if existing.get("updatedAt"):
        merged["updatedAt"] = existing.get("updatedAt")
    if merged.get("manualCaseLinks"):
        merged["subStates"] = [state for state in merged.get("subStates", []) if state != "needs-case-link"]
    if merged.get("manualDistrictLinks"):
        merged["subStates"] = [state for state in merged.get("subStates", []) if state != "needs-district-link"]
    if merged.get("manualPeopleLinks"):
        merged["subStates"] = [state for state in merged.get("subStates", []) if state != "needs-person-link"]
    return merged


def build_batch(root: Path, documents: list[dict], extracts: list[dict], review_tasks: list[dict]) -> dict:
    timestamp = utc_now()
    batch = {
        "id": batch_entity_id(timestamp),
        "type": "ingest_batch",
        "schemaVersion": SCHEMA_VERSION,
        "startedAt": timestamp,
        "finishedAt": timestamp,
        "sourcesScanned": ["intake", "cases/*/*/intake"],
        "docsDiscovered": len(documents),
        "docsParsed": len(extracts),
        "docsApproved": len([task for task in review_tasks if task.get("generalState") == "approved"]),
        "docsDeferred": len([task for task in review_tasks if task.get("generalState") == "deferred"]),
        "docsErrored": len([extract for extract in extracts if extract.get("parseWarnings")]),
        "newDocTypesDetected": len([task for task in review_tasks if "new-doc-type-candidate" in task.get("subStates", [])]),
        "newFieldCandidatesDetected": len([task for task in review_tasks if task.get("newFieldRequests")]),
        "qaSummary": {},
        "parserVersions": {"deterministic": "1.0", "suggestion": "1.0"},
    }
    write_entity(root, "ingest_batches", batch["id"], batch)
    return batch


def build_dashboard(documents: list[dict], attachment_documents: list[dict], extracts: list[dict], suggestions: list[dict], review_tasks: list[dict], cases: list[dict], orgs: list[dict], people: list[dict], batch: dict) -> dict:
    extract_by_doc = {record.get("docId"): record for record in extracts}
    suggestion_by_doc = {record.get("docId"): record for record in suggestions}
    review_by_doc = {record.get("docId"): record for record in review_tasks}
    attachments_by_parent: dict[str, list[dict]] = {}
    for attachment in attachment_documents:
        parent_id = str(attachment.get("parentDocumentId") or "")
        attachments_by_parent.setdefault(parent_id, []).append(attachment)
    detail_rows = []
    for doc in documents:
        detail_rows.append(
            {
                "document": {k: v for k, v in doc.items() if k not in {"messageEntityId", "senderPersonId", "recipientPersonIds", "personIds"}},
                "extract": extract_by_doc.get(doc.get("id"), {}),
                "suggestions": suggestion_by_doc.get(doc.get("id"), {}),
                "review": review_by_doc.get(doc.get("id"), {}),
                "attachmentDocuments": attachments_by_parent.get(str(doc.get("id") or ""), []),
            }
        )
    return {
        "generatedAt": utc_now(),
        "summary": {
            "queueCount": len(review_tasks),
            "documentCount": len(documents),
            "caseCount": len(cases),
            "organizationCount": len(orgs),
            "peopleCount": len(people),
        },
        "batch": batch,
        "queue": [build_queue_item(doc, extract_by_doc.get(doc.get("id"), {}), review_by_doc.get(doc.get("id"), {}), suggestion_by_doc.get(doc.get("id"))) for doc in documents],
        "cases": [
            {
                "id": case.get("id"),
                "caseId": case.get("caseId"),
                "districtCode": case.get("districtCode"),
                "title": case.get("title"),
                "caseType": case.get("caseType"),
                "status": case.get("statusLabel") or case.get("status"),
                "nextDeadline": case.get("nextDeadline"),
            }
            for case in cases
        ],
        "organizations": [{"id": org.get("id"), "name": org.get("name"), "districtCode": org.get("districtCode")} for org in orgs],
        "people": [{"id": person.get("id"), "displayName": person.get("displayName"), "emails": person.get("emails", [])} for person in people],
        "documents": detail_rows,
        "attachmentDocuments": attachment_documents,
        "parserRegistry": _parser_registry(),
        "schemaExpansionQueue": [
            suggestion for suggestion in suggestions if suggestion.get("suggestedNewDocType") or suggestion.get("suggestedNewFieldNames")
        ],
        "fieldTracking": {
            "trackedExtractFields": ["title", "summary", "documentDate", "caseHints", "districtHints", "requestNumbers", "deadlines", "statusSignals"],
            "trackedSuggestionFields": ["suggestedDocType", "suggestedTitle", "suggestedSummary"],
        },
    }


def build_study_email_report(documents: list[dict], extracts: list[dict]) -> dict:
    rows = []
    ext_counter: Counter[str] = Counter()
    process_counter: Counter[str] = Counter()
    docs_by_id = {doc.get("id"): doc for doc in documents}
    for extract in extracts:
        doc = docs_by_id.get(extract.get("docId"), {})
        current_path = str(doc.get("currentPath") or "")
        if not current_path.startswith("intake/study/"):
            continue
        attachments = extract.get("attachments", []) or []
        for attachment in attachments:
            ext = str(attachment.get("extension") or "[noext]")
            ext_counter[ext] += 1
            for signal in attachment.get("processSignals", []) or []:
                process_counter[str(signal)] += 1
        rows.append(
            {
                "docId": extract.get("docId"),
                "path": current_path,
                "title": extract.get("title"),
                "attachmentCount": len(attachments),
                "attachments": attachments,
                "processSignals": extract.get("structuredFields", {}).get("processSignals", []),
            }
        )
    return {
        "emailCount": len(rows),
        "emailsWithAttachments": len([row for row in rows if row.get("attachmentCount")]),
        "attachmentTypes": [{"extension": ext, "count": count} for ext, count in ext_counter.most_common()],
        "attachmentProcessSignals": [{"signal": signal, "count": count} for signal, count in process_counter.most_common()],
        "records": rows,
    }


def _normalize_subject(subject: str) -> str:
    value = (subject or "").strip()
    value = re.sub(r"^(re|fwd?|fw)\s*:\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def _study_stage(signals: list[str]) -> str:
    ordered = [
        ("withdrawal", "withdrawal"),
        ("additional-information", "supplemental-information"),
        ("appeal", "appeal-stage"),
        ("response-sent", "response-stage"),
        ("fee-waiver", "fee-waiver-stage"),
        ("request-filed", "request-stage"),
        ("follow-up", "follow-up-stage"),
        ("settlement", "settlement-stage"),
    ]
    signal_set = set(signals)
    for signal, stage in ordered:
        if signal in signal_set:
            return stage
    return "unclassified"


def build_study_analysis(documents: list[dict], attachment_documents: list[dict], extracts: list[dict], messages: list[dict]) -> dict:
    docs_by_id = {doc.get("id"): doc for doc in documents}
    msg_by_doc = {msg.get("documentId"): msg for msg in messages}
    attachment_by_parent: dict[str, list[dict]] = {}
    for attachment in attachment_documents:
        parent = str(attachment.get("parentDocumentId") or "")
        attachment_by_parent.setdefault(parent, []).append(attachment)

    study_rows = []
    participant_edges = Counter()
    entity_candidates = []
    for extract in extracts:
        doc = docs_by_id.get(extract.get("docId"), {})
        current_path = str(doc.get("currentPath") or "")
        if not current_path.startswith("intake/study/"):
            continue
        msg = msg_by_doc.get(doc.get("id"), {})
        attachments = attachment_by_parent.get(str(doc.get("id") or ""), [])
        participant_names = []
        sender = extract.get("sender") or {}
        if sender.get("email"):
            participant_names.append(sender.get("email"))
        for item in (extract.get("recipients") or []) + (extract.get("cc") or []):
            email = item.get("email")
            if email:
                participant_names.append(email)
            if sender.get("email") and email:
                edge_key = (sender.get("email"), email, "cc" if item in (extract.get("cc") or []) else "to")
                participant_edges[edge_key] += 1
        process_signals = sorted(set((extract.get("structuredFields", {}).get("processSignals") or []) + [sig for attachment in attachments for sig in []]))
        attachment_families = sorted({str(item.get("docType") or item.get("docFamily") or "") for item in attachments if item.get("docType") or item.get("docFamily")})
        stage = _study_stage(process_signals + [sig for att in (extract.get("attachments") or []) for sig in (att.get("processSignals") or [])])
        normalized_subject = _normalize_subject(extract.get("subjectLine") or extract.get("title") or "")
        case_hints = extract.get("caseHints") or []
        district_hints = extract.get("districtHints") or []
        row = {
            "docId": doc.get("id"),
            "path": current_path,
            "subject": extract.get("subjectLine") or extract.get("title"),
            "normalizedSubject": normalized_subject,
            "sentAt": msg.get("sentAt") or extract.get("documentDate") or "",
            "sender": sender,
            "participants": participant_names,
            "caseHints": case_hints,
            "districtHints": district_hints,
            "processSignals": process_signals,
            "attachmentFamilies": attachment_families,
            "attachmentDocIds": [item.get("id") for item in attachments],
            "combinedStage": stage,
            "threadKey": msg.get("threadKey") or extract.get("structuredFields", {}).get("threadKey") or "",
        }
        study_rows.append(row)
        for email in participant_names:
            if email.endswith("@attleboroschools.com"):
                entity_candidates.append({
                    "targetType": "person",
                    "targetKey": email,
                    "sourceDocId": doc.get("id"),
                    "candidateType": "contact-profile-fill",
                    "suggestedFields": {"emails": [email], "awarenessSignals": process_signals, "districtHints": district_hints},
                })

    threads: dict[str, dict] = {}
    for row in study_rows:
        cluster_key = row.get("threadKey") or row.get("normalizedSubject") or row.get("docId")
        entry = threads.setdefault(
            cluster_key,
            {
                "clusterId": f"study-thread:{slugify(cluster_key)}",
                "threadKey": row.get("threadKey") or "",
                "normalizedSubject": row.get("normalizedSubject"),
                "docIds": [],
                "subjects": [],
                "participants": set(),
                "caseHints": set(),
                "districtHints": set(),
                "stages": Counter(),
                "attachmentDocIds": [],
                "sentAt": [],
            },
        )
        entry["docIds"].append(row.get("docId"))
        entry["subjects"].append(row.get("subject"))
        entry["participants"].update(row.get("participants", []))
        entry["caseHints"].update(row.get("caseHints", []))
        entry["districtHints"].update(row.get("districtHints", []))
        entry["stages"][row.get("combinedStage", "unclassified")] += 1
        entry["attachmentDocIds"].extend(row.get("attachmentDocIds", []))
        if row.get("sentAt"):
            entry["sentAt"].append(row.get("sentAt"))

    thread_records = []
    for cluster in threads.values():
        dates = sorted(cluster["sentAt"])
        dominant_stage = cluster["stages"].most_common(1)[0][0] if cluster["stages"] else "unclassified"
        thread_records.append(
            {
                "clusterId": cluster["clusterId"],
                "threadKey": cluster["threadKey"],
                "normalizedSubject": cluster["normalizedSubject"],
                "docIds": cluster["docIds"],
                "subjects": sorted(set(cluster["subjects"])),
                "participants": sorted(cluster["participants"]),
                "caseHints": sorted(cluster["caseHints"]),
                "districtHints": sorted(cluster["districtHints"]),
                "attachmentDocIds": sorted(set(cluster["attachmentDocIds"])),
                "dominantStage": dominant_stage,
                "dateRange": {"first": dates[0] if dates else "", "last": dates[-1] if dates else ""},
                "stageCounts": [{"stage": key, "count": value} for key, value in cluster["stages"].most_common()],
            }
        )

    timeline_candidates = sorted(
        [
            {
                "docId": row.get("docId"),
                "date": row.get("sentAt"),
                "title": row.get("subject"),
                "stage": row.get("combinedStage"),
                "caseHints": row.get("caseHints"),
                "districtHints": row.get("districtHints"),
                "attachmentDocIds": row.get("attachmentDocIds"),
                "processSignals": row.get("processSignals"),
            }
            for row in study_rows
        ],
        key=lambda item: item.get("date") or "",
    )

    participant_graph = {
        "edges": [
            {"from": edge[0], "to": edge[1], "relation": edge[2], "count": count}
            for edge, count in participant_edges.most_common()
        ]
    }

    return {
        "threads": thread_records,
        "combinedEvents": study_rows,
        "timelineCandidates": timeline_candidates,
        "participantGraph": participant_graph,
        "entityCandidates": entity_candidates,
    }


def build_approved_events(documents: list[dict], extracts: list[dict], review_tasks: list[dict]) -> list[dict]:
    extract_by_doc = {record.get("docId"): record for record in extracts}
    approved_events: list[dict] = []
    for task in review_tasks:
        if task.get("generalState") not in {"approved", "completed"}:
            continue
        doc_id = task.get("docId")
        extract = extract_by_doc.get(doc_id, {})
        case_links = task.get("manualCaseLinks") or extract.get("caseHints", [])
        district_links = task.get("manualDistrictLinks") or extract.get("districtHints", [])
        if not case_links:
            continue
        for case_id in case_links:
            approved_events.append(
                {
                    "eventId": f"event:{slugify(case_id)}:{slugify(doc_id or '')}",
                    "caseId": case_id,
                    "districtCode": district_links[0] if district_links else "",
                    "eventType": extract.get("docFamily") or "document",
                    "eventDate": extract.get("documentDate") or "",
                    "datePrecision": extract.get("datePrecision") or "unknown",
                    "title": extract.get("title") or doc_id,
                    "description": extract.get("summary") or "Approved ingest document event.",
                    "documents": [doc_id],
                    "derivedFromDocIds": [doc_id],
                    "statusImpact": None,
                    "deadlineImpact": None,
                    "visibility": "internal",
                    "confidence": extract.get("confidence") or 0.5,
                    "approved": True,
                }
            )
    return approved_events


def _mime_from_extension(extension: str) -> str:
    return {
        ".eml": "message/rfc822",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".json": "application/json",
        ".mp3": "audio/mpeg",
    }.get(extension, "application/octet-stream")


def _parser_registry() -> list[dict]:
    return [
        {"docFamily": "email", "docType": "email-correspondence", "parserModule": "skills.ingest.parsers.email", "version": "1.0", "status": "active", "requiredFields": ["documentDate", "sender"], "optionalFields": ["attachments", "caseHints"], "supportsAiAssist": True, "reviewRequiredByDefault": True},
        {"docFamily": "public-records", "docType": "public-records-document", "parserModule": "skills.ingest.parsers.public_records", "version": "1.0", "status": "active", "requiredFields": ["title"], "optionalFields": ["requestNumbers", "statusSignals"], "supportsAiAssist": True, "reviewRequiredByDefault": True},
        {"docFamily": "prs", "docType": "prs-related-document", "parserModule": "skills.ingest.parsers.prs", "version": "1.0", "status": "active", "requiredFields": ["title"], "optionalFields": ["actionsOrdered"], "supportsAiAssist": True, "reviewRequiredByDefault": True},
        {"docFamily": "determination", "docType": "formal-determination", "parserModule": "skills.ingest.parsers.determination", "version": "1.0", "status": "active", "requiredFields": ["title"], "optionalFields": ["determinationOutcome"], "supportsAiAssist": True, "reviewRequiredByDefault": True},
    ]


def run_ingest_pipeline(root: Path) -> dict:
    ensure_ingest_dirs(root)
    rules_bundle = load_all_rules(root)
    cases = build_case_entities(root)
    orgs = build_org_entities(root, cases)
    documents = discover_documents(root)
    extracts, suggestions, people, messages, links, attachment_documents = parse_documents(root, documents, rules_bundle)
    for message in messages:
        if message.get("id"):
            write_entity(root, "messages", message["id"], message)
    for attachment in attachment_documents:
        if attachment.get("id"):
            write_entity(root, "documents", attachment["id"], attachment)
    build_people_entities(root, people)

    existing_review_tasks = load_existing_review_tasks(root)
    review_tasks = []
    for doc, extract in zip(documents, extracts):
        doc_id = str(doc.get("id") or "")
        suggestion = next((s for s in suggestions if s.get("docId") == doc.get("id")), None)
        fresh_task = build_review_task(doc, extract, suggestion)
        review_tasks.append(merge_review_task(existing_review_tasks.get(doc_id), fresh_task))
    for task in review_tasks:
        write_entity(root, "review_tasks", task["id"], task)

    batch = build_batch(root, documents, extracts, review_tasks)
    qa_summary = summarize_qa(documents, extracts, review_tasks)
    batch["qaSummary"] = qa_summary
    write_entity(root, "ingest_batches", batch["id"], batch)

    append_jsonl(root / EDGE_ROOT / "entity_links.jsonl", links)
    append_jsonl(root / EDGE_ROOT / "message_participants.jsonl", [link for link in links if link.get("toType") == "message"])

    write_json(root / INGEST_ROOT / "document_extracts.json", {"records": extracts})
    write_json(root / INGEST_ROOT / "document_suggestions.json", {"records": suggestions})
    write_json(root / INGEST_ROOT / "ingest_queue.json", {"records": [build_queue_item(doc, extract, task, next((s for s in suggestions if s.get('docId') == doc.get('id')), None)) for doc, extract, task in zip(documents, extracts, review_tasks)]})
    write_json(root / INGEST_ROOT / "parser_registry.json", {"records": _parser_registry()})
    write_json(root / INGEST_ROOT / "schema_expansion_queue.json", {"records": [s for s in suggestions if s.get("suggestedNewDocType") or s.get("suggestedNewFieldNames")]})
    write_json(root / INGEST_ROOT / "rule_sets.json", rules_bundle)
    write_json(
        root / INGEST_ROOT / "rule_matches.json",
        {
            "records": [
                {
                    "docId": doc.get("id"),
                    "docFamily": doc.get("docFamily"),
                    "docType": doc.get("docType"),
                    "matchedRuleIds": doc.get("matchedRuleIds", []),
                    "matchedRuleSources": doc.get("matchedRuleSources", []),
                }
                for doc in documents
            ]
        },
    )

    run_history = read_json(root / INGEST_ROOT / "run_history.json", default={"records": []})
    run_history_records = [batch] + run_history.get("records", [])[:19]
    write_json(root / INGEST_ROOT / "run_history.json", {"records": run_history_records})

    dashboard = build_dashboard(documents, attachment_documents, extracts, suggestions, review_tasks, cases, orgs, people, batch)
    write_json(root / INGEST_ROOT / "review_dashboard.json", dashboard)
    write_json(root / INGEST_ROOT / "review_queue.json", {"records": review_tasks})
    write_json(root / INGEST_ROOT / "approved_events.json", {"records": build_approved_events(documents, extracts, review_tasks)})
    write_json(root / INGEST_ROOT / "study_email_report.json", build_study_email_report(documents, extracts))
    write_json(root / INGEST_ROOT / "attachment_documents.json", {"records": attachment_documents})
    study_analysis = build_study_analysis(documents, attachment_documents, extracts, messages)
    write_json(root / INGEST_ROOT / "study_threads.json", {"records": study_analysis.get("threads", [])})
    write_json(root / INGEST_ROOT / "study_combined_events.json", {"records": study_analysis.get("combinedEvents", [])})
    write_json(root / INGEST_ROOT / "study_timeline_candidates.json", {"records": study_analysis.get("timelineCandidates", [])})
    write_json(root / INGEST_ROOT / "study_participant_graph.json", study_analysis.get("participantGraph", {}))
    write_json(root / INGEST_ROOT / "study_entity_candidates.json", {"records": study_analysis.get("entityCandidates", [])})

    return {
        "documents": len(documents),
        "attachmentDocuments": len(attachment_documents),
        "studyThreads": len(study_analysis.get("threads", [])),
        "cases": len(cases),
        "organizations": len(orgs),
        "people": len(people),
        "reviewTasks": len(review_tasks),
        "newDocTypeCandidates": len([task for task in review_tasks if "new-doc-type-candidate" in task.get("subStates", [])]),
        "docFamilyRuleCount": len(rules_bundle.get("doc-families", [])),
        "situationRuleCount": len(rules_bundle.get("situations", [])),
    }
