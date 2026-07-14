from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from ..common import ensure_dir, read_json, slugify, write_json


SCHEMA_VERSION = "1.0"
INGEST_ROOT = Path("data") / "derived" / "ingest"
ENTITY_ROOT = Path("data") / "entities"
EDGE_ROOT = Path("data") / "edges"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def typed_id(prefix: str, value: str) -> str:
    return f"{prefix}:{value}"


def rel_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def doc_id_for_hash(sha256: str) -> str:
    return typed_id("doc", f"sha256:{sha256}")


def case_entity_id(case_id: str) -> str:
    return typed_id("case", case_id)


def org_entity_id(code: str) -> str:
    return typed_id("org", code)


def person_entity_id(name: str, email: str = "") -> str:
    token = slugify(email or name)
    return typed_id("person", token)


def message_entity_id(message_id: str, fallback: str) -> str:
    token = sha256_text(message_id or fallback)[:16]
    return typed_id("msg", token)


def task_entity_id(doc_id: str) -> str:
    token = sha256_text(doc_id)[:16]
    return typed_id("task", token)


def batch_entity_id(timestamp: str) -> str:
    token = re.sub(r"[^0-9A-Za-z]+", "", timestamp)
    return typed_id("batch", token.lower())


def ensure_ingest_dirs(root: Path) -> None:
    for rel in [
        ENTITY_ROOT / "cases",
        ENTITY_ROOT / "orgs",
        ENTITY_ROOT / "people",
        ENTITY_ROOT / "documents",
        ENTITY_ROOT / "messages",
        ENTITY_ROOT / "events",
        ENTITY_ROOT / "review_tasks",
        ENTITY_ROOT / "ingest_batches",
        INGEST_ROOT,
        EDGE_ROOT,
    ]:
        ensure_dir(root / rel)


def write_entity(root: Path, entity_type: str, entity_id: str, payload: dict) -> None:
    ensure_ingest_dirs(root)
    path = root / ENTITY_ROOT / entity_type / f"{slugify(entity_id)}.json"
    write_json(path, payload)


def append_jsonl(path: Path, records: list[dict]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def load_case_metadata(root: Path) -> list[dict]:
    records = []
    for path in sorted(root.glob("cases/*/*/metadata.json")):
        payload = read_json(path, default={})
        if payload:
            payload["sourceMetadata"] = rel_path(path, root)
            records.append(payload)
    return records


def normalize_email_address(value: str) -> str:
    return (value or "").strip().lower()


def first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None
