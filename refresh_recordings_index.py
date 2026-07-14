from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
CASE_ID = "ATTLEBORO-PRR-002"
CASE_BASE = ROOT / "cases" / "ATTLEBORO" / CASE_ID
RECORDINGS_DIR = CASE_BASE / "recordings"
MANIFEST_FILE = CASE_BASE / "attachments" / "2026-03-19_Attachment_ATTLEBORO-PRR-002_Audio_Manifest.txt"
INDEX_FILE = CASE_BASE / "recordings_index.json"


def safe_name(value: str) -> str:
    safe = []
    for ch in value:
        if ch.isalnum() or ch in {"-", "_", "."}:
            safe.append(ch)
        elif ch in {" ", "/"}:
            safe.append("_")
    out = "".join(safe).strip("_")
    return out or "file"


def parse_date_token(stem: str) -> tuple[str, str, bool]:
    m = re.match(r"(\d{4}-\d{2}-\d{2})_", stem)
    if m:
        return m.group(1), "day", "_Estimated_" in stem

    m = re.match(r"(\d{4}-\d{2})_", stem)
    if m:
        return m.group(1), "month", "_Estimated_" in stem

    return "", "unknown", True


def normalize_committee(raw: str) -> str:
    committee = raw.replace("_", " ").strip()
    committee = re.sub(r"\s+", " ", committee)
    if committee.lower().startswith("and learning"):
        committee = "Teaching & Learning"
    if committee.lower() == "school comm":
        committee = "Emergency School Comm"
    if re.fullmatch(r"\d+", committee):
        committee = "Unknown (Estimated)"
    committee = committee.replace("and", "&")
    committee = committee.replace("Finanace", "Finance")
    return committee


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


def backfill_undated_names() -> int:
    if not RECORDINGS_DIR.exists():
        return 0

    renamed = 0
    for mp3 in sorted(RECORDINGS_DIR.glob("undated_Recording_*.mp3")):
        mtime = mp3.stat().st_mtime
        # Use filesystem modified date as fallback estimate.
        date_prefix = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

        marker = f"undated_Recording_{CASE_ID}_"
        if not mp3.stem.startswith(marker):
            continue
        rest = mp3.stem[len(marker) :]
        new_stem = safe_name(f"{date_prefix}_Estimated_Recording_{CASE_ID}_{rest}")
        target = unique_path(mp3.with_name(f"{new_stem}.mp3"))
        mp3.rename(target)
        renamed += 1

    return renamed


def build_index() -> list[dict]:
    records = []
    for mp3 in sorted(RECORDINGS_DIR.glob("*.mp3")):
        stem = mp3.stem
        date_value, precision, estimated = parse_date_token(stem)

        committee = "Unknown"
        marker = f"_Recording_{CASE_ID}_"
        if marker in stem:
            committee_raw = stem.split(marker, 1)[1]
            committee = normalize_committee(committee_raw)

        records.append(
            {
                "fileName": mp3.name,
                "relativePath": str(mp3.relative_to(ROOT)).replace("\\", "/"),
                "date": date_value,
                "datePrecision": precision,
                "dateEstimated": estimated,
                "committee": committee,
                "sizeBytes": mp3.stat().st_size,
            }
        )

    records.sort(key=lambda r: (r["date"] or "9999-99-99", r["committee"], r["fileName"]))
    return records


def write_outputs(records: list[dict]) -> None:
    INDEX_FILE.write_text(json.dumps({"caseId": CASE_ID, "total": len(records), "recordings": records}, indent=2), encoding="utf-8")
    MANIFEST_FILE.write_text("\n".join(r["relativePath"] for r in records) + "\n", encoding="utf-8")


def main() -> None:
    renamed = backfill_undated_names()
    records = build_index()
    write_outputs(records)
    print(f"Renamed undated recordings: {renamed}")
    print(f"Indexed recordings: {len(records)}")


if __name__ == "__main__":
    main()
