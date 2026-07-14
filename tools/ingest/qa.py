from __future__ import annotations


def summarize_qa(documents: list[dict], extracts: list[dict], review_tasks: list[dict]) -> dict:
    review_by_doc = {task.get("docId"): task for task in review_tasks}
    missing_case_links = len(
        [
            record
            for record in extracts
            if not ((review_by_doc.get(record.get("docId"), {}) or {}).get("manualCaseLinks") or record.get("caseHints"))
        ]
    )
    missing_dates = len([record for record in extracts if not record.get("documentDate")])
    warnings = len([record for record in extracts if record.get("parseWarnings")])
    high_priority = len([task for task in review_tasks if task.get("priority") == "high"])
    return {
        "documentCount": len(documents),
        "extractCount": len(extracts),
        "reviewTaskCount": len(review_tasks),
        "missingCaseLinks": missing_case_links,
        "missingDates": missing_dates,
        "parserWarnings": warnings,
        "highPriorityReviewCount": high_priority,
    }
