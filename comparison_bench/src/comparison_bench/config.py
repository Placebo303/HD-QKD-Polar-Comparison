from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _parse_scalar(value: str) -> Any:
    v = value.strip()
    if v in ("", "null", "None", "~"):
        return None
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [] if not inner else [_parse_scalar(x.strip()) for x in inner.split(",")]
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def _minimal_yaml(text: str) -> dict[str, Any]:
    # Tiny parser for the repository's simple benchmark configs. PyYAML is preferred when installed.
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            item_text = line[2:].strip()
            if not isinstance(parent, list):
                raise ValueError(f"Unsupported YAML list placement: {raw}")
            if ":" in item_text:
                key, val = item_text.split(":", 1)
                item: dict[str, Any] = {key.strip(): _parse_scalar(val) if val.strip() else {}}
                parent.append(item)
                stack.append((indent, item))
            else:
                parent.append(_parse_scalar(item_text))
            continue
        if ":" not in line:
            raise ValueError(f"Unsupported YAML line: {raw}")
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val:
            parent[key] = _parse_scalar(val)
        else:
            next_container: Any = [] if key.endswith("s") and key in {"datasets", "methods"} else {}
            parent[key] = next_container
            stack.append((indent, next_container))
    return root


def load_config(path: Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        obj = json.loads(text)
    else:
        try:
            import yaml  # type: ignore
            obj = yaml.safe_load(text)
        except ImportError:
            obj = _minimal_yaml(text)
    if not isinstance(obj, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return obj


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
