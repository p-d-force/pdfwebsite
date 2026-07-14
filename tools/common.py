"""
Common utilities for skills modules.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Root directory of the project
ROOT = Path(__file__).parent.parent


def read_json(filepath: Union[str, Path]) -> Any:
    """Read JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(filepath: Union[str, Path], data: Any, indent: int = 2) -> None:
    """Write JSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(text: str, separator: str = "-") -> str:
    """Convert text to URL-safe slug."""
    if not text:
        return ""
    
    # Normalize Unicode
    text = unicodedata.normalize("NFKD", text)
    
    # Remove non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace non-alphanumeric characters with separator
    text = re.sub(r"[^\w\s-]", "", text)
    
    # Replace whitespace and multiple separators
    text = re.sub(r"[-\s]+", separator, text)
    
    # Remove leading/trailing separators
    text = text.strip(separator)
    
    return text
