from __future__ import annotations

from pathlib import Path

from ..common import read_json


def load_rule_registry(root: Path) -> dict:
    return read_json(root / "config" / "ingest_rules" / "registry.json", default={})


def load_rules(root: Path, group: str) -> list[dict]:
    registry = load_rule_registry(root)
    key = "docFamilyRuleDir" if group == "doc-families" else "situationRuleDir"
    rel = registry.get(key)
    if not rel:
        return []
    rule_dir = root / rel
    if not rule_dir.exists():
        return []
    rules = []
    for path in sorted(rule_dir.glob("*.json")):
        payload = read_json(path, default={})
        if payload:
            payload["sourcePath"] = str(path.relative_to(root)).replace("\\", "/")
            rules.append(payload)
    return rules


def load_all_rules(root: Path) -> dict[str, list[dict]]:
    return {
        "doc-families": load_rules(root, "doc-families"),
        "situations": load_rules(root, "situations"),
    }


def match_doc_family_rules(doc: dict, rules: list[dict]) -> list[dict]:
    matches = []
    doc_family = doc.get("docFamily")
    extension = doc.get("extension")
    for rule in rules:
        rule_match = rule.get("match", {})
        allowed_families = rule_match.get("docFamilies", [])
        allowed_extensions = rule_match.get("extensions", [])
        if allowed_families and doc_family not in allowed_families:
            continue
        if allowed_extensions and extension not in allowed_extensions:
            continue
        matches.append(rule)
    return sorted(matches, key=lambda item: item.get("priority", 0), reverse=True)
