from __future__ import annotations

import email
from email.header import decode_header
from email.message import Message
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import argparse


ROOT = Path(__file__).resolve().parent
INTAKE_DIR = ROOT / "intake"
LOG_FILE = ROOT / "cases" / "_ingest_log.json"


LEGACY_FILE_MAP = {
    "Public Records Request – Hiring Records for School Adjustment Counselor Position at Silvia Elementary.eml": {
        "district": "FALLRIVER",
        "case_id": "FALLRIVER-PRR-001",
        "eml_name": "2026-03-19_Correspondence_FALLRIVER-PRR-001_Hiring_Records_Clarification.eml",
        "attachment_date": "2026-03-19",
        "attachment_type": "Attachment",
        "attachment_desc": "Source_Document",
        "attachment_folder": "attachments",
    },
    "Public Records Request #2.eml": {
        "district": "FALLRIVER",
        "case_id": "FALLRIVER-PRR-002",
        "eml_name": "2026-03-19_Correspondence_FALLRIVER-PRR-002_Request_Acknowledgement.eml",
        "attachment_date": "2026-03-19",
        "attachment_type": "Attachment",
        "attachment_desc": "Source_Document",
        "attachment_folder": "attachments",
    },
    "3.19.2026 PRS 15514 Fall River RLR.eml": {
        "district": "FALLRIVER",
        "case_id": "PRS-15514",
        "eml_name": "2026-03-19_Correspondence_PRS-15514_Request_for_Local_Response.eml",
        "attachment_date": "2026-03-19",
        "attachment_type": "Determination",
        "attachment_desc": "Request_for_Local_Response",
        "attachment_folder": "determinations",
    },
}


SUBFOLDERS = [
    "original-request",
    "appeals",
    "determinations",
    "correspondence",
    "attachments",
    "recordings",
]


def decode_filename(raw_name: str) -> str:
    parts = decode_header(raw_name)
    decoded = []
    for text, encoding in parts:
        if isinstance(text, bytes):
            decoded.append(text.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded.append(text)
    return "".join(decoded)


def safe_name(value: str) -> str:
    safe = []
    for ch in value:
        if ch.isalnum() or ch in {"-", "_", "."}:
            safe.append(ch)
        elif ch in {" ", "/"}:
            safe.append("_")
    out = "".join(safe).strip("_")
    return out or "file"


def ensure_case_dirs(case_base: Path) -> None:
    case_base.mkdir(parents=True, exist_ok=True)
    for folder in SUBFOLDERS:
        (case_base / folder).mkdir(parents=True, exist_ok=True)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    idx = 2
    while True:
        candidate = path.with_name(f"{stem}_{idx}{suffix}")
        if not candidate.exists():
            return candidate
        idx += 1


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def same_bytes(a: Path, b: Path) -> bool:
    if not a.exists() or not b.exists() or a.stat().st_size != b.stat().st_size:
        return False
    return a.read_bytes() == b.read_bytes()


def decode_subject(msg: Message) -> str:
    raw = msg.get("Subject") or ""
    return decode_filename(raw)


def normalize_case_id(case_id: str) -> str:
    return case_id.strip().upper()


def classify_eml(source: Path, msg: Message) -> dict | None:
    if source.name in LEGACY_FILE_MAP:
        cfg = dict(LEGACY_FILE_MAP[source.name])
        cfg["case_id"] = normalize_case_id(cfg["case_id"])
        return cfg

    subject = decode_subject(msg).lower()
    from_addr = (msg.get("From") or "").lower()
    to_addr = (msg.get("To") or "").lower()

    if "prr - 03-11-26" in subject and "attleboroschools" in from_addr:
        return {
            "district": "ATTLEBORO",
            "case_id": "SPR26-0842",
            "eml_name": "2026-03-19_Correspondence_SPR26-0842_District_Response_to_Narrowed_Scope.eml",
            "attachment_date": "2026-03-19",
            "attachment_type": "Attachment",
            "attachment_desc": "Response_Document",
            "attachment_folder": "attachments",
        }

    if (
        "recordings/transcripts/minutes/materials" in subject
        and "apsrao@attleboroschools.com" in to_addr
    ):
        return {
            "district": "ATTLEBORO",
            "case_id": "ATTLEBORO-PRR-002",
            "eml_name": "2026-01-31_Correspondence_ATTLEBORO-PRR-002_Broad_Meeting_Records_Request.eml",
            "attachment_date": "2026-01-31",
            "attachment_type": "Attachment",
            "attachment_desc": "Source_Document",
            "attachment_folder": "attachments",
        }

    return None


def destination_for_attachment(cfg: dict, original_name: str) -> tuple[str, str]:
    lower = original_name.lower()

    if cfg["district"] == "ATTLEBORO" and cfg["case_id"] == "SPR26-0842":
        if lower.endswith(".pdf"):
            return (
                "correspondence",
                "2026-03-19_Correspondence_SPR26-0842_District_Response_Letter.pdf",
            )
        if lower.endswith(".xlsx"):
            return (
                "attachments",
                "2026-03-19_Attachment_SPR26-0842_PD_Database_Export.xlsx",
            )

    ext = Path(original_name).suffix.lower() or ".bin"
    generic = safe_name(
        f"{cfg['attachment_date']}_{cfg['attachment_type']}_{cfg['case_id']}_{cfg['attachment_desc']}{ext}"
    )
    return cfg["attachment_folder"], generic


def write_deduped_bytes(target: Path, data: bytes, ingest_log: dict, dry_run: bool = False) -> Path | None:
    digest = sha256_bytes(data)
    known = ingest_log.setdefault("file_hashes", {}).get(digest)
    if known:
        known_path = ROOT / known
        if known_path.exists():
            return None

    final_target = unique_path(target)
    if dry_run:
        return final_target

    final_target.write_bytes(data)
    ingest_log.setdefault("file_hashes", {})[digest] = str(final_target.relative_to(ROOT)).replace("\\", "/")
    return final_target


def extract_attachments(msg: Message, cfg: dict, dry_run: bool = False) -> list[str]:
    extracted = []

    for part in msg.walk():
        raw_name = part.get_filename()
        if not raw_name:
            continue

        filename = decode_filename(raw_name)
        content_type = (part.get_content_type() or "").lower()
        disposition = (part.get("Content-Disposition") or "").lower()

        if content_type.startswith("image/"):
            continue
        if "inline" in disposition and not filename.lower().endswith((".pdf", ".doc", ".docx", ".xlsx", ".csv", ".txt")):
            continue

        payload = part.get_payload(decode=True)
        if not payload or not isinstance(payload, (bytes, bytearray)):
            continue

        target_folder, target_name = destination_for_attachment(cfg, filename)
        target_dir = ROOT / "cases" / cfg["district"] / cfg["case_id"] / target_folder
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        written = write_deduped_bytes(
            target_dir / safe_name(target_name),
            bytes(payload),
            cfg["ingest_log"],
            dry_run=dry_run,
        )
        if written:
            extracted.append(str(written.relative_to(ROOT)).replace("\\", "/"))

    return extracted


def normalize_committee(name: str) -> str:
    normalized = name.strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace("&", "and")
    normalized = normalized.replace("Finanace", "Finance")
    return normalized


def extract_date_token(filename: str) -> str:
    m = re.search(r"(\d{2})(\d{2})(\d{2})", filename)
    if m:
        yy, mm, dd = m.groups()
        year = 2000 + int(yy)
        return f"{year:04d}-{int(mm):02d}-{int(dd):02d}"

    m = re.search(r"(\d{2})-(\d{2})-(\d{2})", filename)
    if m:
        mm, dd, yy = m.groups()
        year = 2000 + int(yy)
        return f"{year:04d}-{int(mm):02d}-{int(dd):02d}"

    m = re.search(
        r"(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sept|sep|october|oct|november|nov|december|dec)\s+(\d{4})",
        filename,
        flags=re.IGNORECASE,
    )
    if m:
        month_name, year = m.groups()
        months = {
            "january": 1,
            "jan": 1,
            "february": 2,
            "feb": 2,
            "march": 3,
            "mar": 3,
            "april": 4,
            "apr": 4,
            "may": 5,
            "june": 6,
            "jun": 6,
            "july": 7,
            "jul": 7,
            "august": 8,
            "aug": 8,
            "september": 9,
            "sept": 9,
            "sep": 9,
            "october": 10,
            "oct": 10,
            "november": 11,
            "nov": 11,
            "december": 12,
            "dec": 12,
        }
        return f"{int(year):04d}-{months[month_name.lower()]:02d}"

    return "undated"


def ingest_audio_files(ingest_log: dict, dry_run: bool = False) -> list[str]:
    cfg = {
        "district": "ATTLEBORO",
        "case_id": "ATTLEBORO-PRR-002",
    }
    case_base = ROOT / "cases" / cfg["district"] / cfg["case_id"]
    ensure_case_dirs(case_base)

    moved = []
    recordings_dir = case_base / "recordings"

    for source in sorted(INTAKE_DIR.glob("*.MP3")):
        data = source.read_bytes()
        digest = sha256_bytes(data)
        known = ingest_log.setdefault("file_hashes", {}).get(digest)
        if known and (ROOT / known).exists():
            if dry_run:
                continue
            source.unlink(missing_ok=True)
            continue

        base = source.stem
        committee = base.split("-")[0].strip() if "-" in base else base
        committee = normalize_committee(committee)
        date_token = extract_date_token(base)
        out_name = safe_name(
            f"{date_token}_Recording_ATTLEBORO-PRR-002_{committee}.mp3"
        )
        target = unique_path(recordings_dir / out_name)

        if not dry_run:
            shutil.move(str(source), str(target))
            ingest_log.setdefault("file_hashes", {})[digest] = str(target.relative_to(ROOT)).replace("\\", "/")
        moved.append(str(target.relative_to(ROOT)).replace("\\", "/"))

    if moved and not dry_run:
        manifest = case_base / "attachments" / "2026-03-19_Attachment_ATTLEBORO-PRR-002_Audio_Manifest.txt"
        manifest.write_text("\n".join(moved) + "\n", encoding="utf-8")

    return moved


def ingest(dry_run: bool = False) -> None:
    if not INTAKE_DIR.exists():
        print("No intake directory found.")
        return

    if LOG_FILE.exists():
        ingest_log = json.loads(LOG_FILE.read_text(encoding="utf-8"))
    else:
        ingest_log = {"message_ids": {}, "file_hashes": {}}

    ingest_log.setdefault("message_ids", {})
    ingest_log.setdefault("file_hashes", {})

    for existing_eml in (ROOT / "cases").rglob("*.eml"):
        existing_msg = email.message_from_bytes(existing_eml.read_bytes())
        existing_id = (existing_msg.get("Message-ID") or "").strip()
        if existing_id:
            ingest_log.setdefault("message_ids", {})[existing_id] = str(existing_eml.relative_to(ROOT)).replace("\\", "/")

    processed = []
    skipped = []
    deduped = []

    for source in sorted(INTAKE_DIR.glob("*.eml")):
        src_bytes = source.read_bytes()
        src_msg = email.message_from_bytes(src_bytes)
        cfg = classify_eml(source, src_msg)
        if not cfg:
            skipped.append(source.name)
            continue

        cfg = dict(cfg)
        cfg["ingest_log"] = ingest_log
        msg_id = (src_msg.get("Message-ID") or "").strip()
        eml_digest = sha256_bytes(src_bytes)
        if msg_id and msg_id in ingest_log.get("message_ids", {}):
            if not dry_run:
                source.unlink(missing_ok=True)
            deduped.append(source.name)
            continue
        known_by_hash = ingest_log.get("file_hashes", {}).get(eml_digest)
        if known_by_hash and (ROOT / known_by_hash).exists():
            if not dry_run:
                source.unlink(missing_ok=True)
            deduped.append(source.name)
            continue

        case_base = ROOT / "cases" / cfg["district"] / cfg["case_id"]
        ensure_case_dirs(case_base)

        eml_dest = case_base / "correspondence" / cfg["eml_name"]
        eml_dest = unique_path(eml_dest)

        if eml_dest.exists() and same_bytes(source, eml_dest):
            if not dry_run:
                source.unlink()
            extracted = []
        else:
            if dry_run:
                extracted = extract_attachments(src_msg, cfg, dry_run=True)
            else:
                shutil.move(str(source), str(eml_dest))
                moved_msg = email.message_from_bytes(eml_dest.read_bytes())
                extracted = extract_attachments(moved_msg, cfg, dry_run=False)

        if msg_id and not dry_run:
            ingest_log.setdefault("message_ids", {})[msg_id] = str(eml_dest.relative_to(ROOT)).replace("\\", "/")
        if not dry_run:
            ingest_log.setdefault("file_hashes", {})[eml_digest] = str(eml_dest.relative_to(ROOT)).replace("\\", "/")

        processed.append((str(eml_dest.relative_to(ROOT)).replace("\\", "/"), extracted))

    moved_audio = ingest_audio_files(ingest_log, dry_run=dry_run)

    if moved_audio and not dry_run:
        refresh_script = ROOT / "refresh_recordings_index.py"
        if refresh_script.exists():
            subprocess.run([sys.executable, str(refresh_script)], check=False)

    if not dry_run:
        LOG_FILE.write_text(json.dumps(ingest_log, indent=2), encoding="utf-8")

    print("Processed files:")
    for eml_rel, extracted in processed:
        print(f"- {eml_rel}")
        for attach_rel in extracted:
            print(f"  * {attach_rel}")

    if skipped:
        print("Skipped (no mapping):")
        for item in skipped:
            print(f"- {item}")

    if deduped:
        print("Deduped (already ingested by Message-ID):")
        for item in deduped:
            print(f"- {item}")

    if moved_audio:
        print("Moved audio files:")
        for item in moved_audio:
            print(f"- {item}")

    if dry_run:
        print("Dry run complete. No files were moved, deleted, or written.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest intake EML/audio files into case archive.")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without modifying files")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    ingest(dry_run=args.dry_run)
