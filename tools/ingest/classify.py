from __future__ import annotations

from pathlib import Path


def classify_document(file_name: str, extension: str, path_hint: str = "") -> tuple[str, str, float]:
    text = f"{file_name} {path_hint}".lower()

    if extension == ".eml":
        return ("email", "email-correspondence", 0.99)
    if extension in {".xlsx", ".xls", ".csv"}:
        return ("spreadsheet", "tabular-attachment", 0.97)
    if "spr" in text and any(token in text for token in ["additional information", "supplemental", "appeal", "spr25", "spr26"]):
        return ("determination", "spr-process-document", 0.91)
    if "prs" in text:
        if "local_response" in text or "local response" in text:
            return ("prs", "prs-local-response-request", 0.95)
        return ("prs", "prs-related-document", 0.88)
    if "determination" in text:
        return ("determination", "formal-determination", 0.95)
    if any(token in text for token in ["response letter", "district response", "rao response", "response - prr", "prr response"]):
        return ("public-records", "district-response-document", 0.93)
    if any(token in text for token in ["affidavit", "fee waiver", "indigency"]):
        return ("public-records", "fee-waiver-supporting-document", 0.92)
    if any(token in text for token in ["appendix", "appendices", "exhibit"]):
        return ("attachment", "appendix-or-exhibit", 0.85)
    if extension == ".zip" and any(token in text for token in ["prr", "response", "request", "records"]):
        return ("public-records", "response-package", 0.94)
    if "appeal" in text or "request" in text or "prr" in text or "records" in text:
        return ("public-records", "public-records-document", 0.9)
    if "correspondence" in text or "notice" in text or "email" in text:
        return ("correspondence", "general-correspondence", 0.82)
    if extension in {".pdf", ".doc", ".docx", ".txt", ".json", ".mp3", ".zip"}:
        return ("attachment", "generic-attachment", 0.55)
    return ("unknown", "unknown-document", 0.15)
