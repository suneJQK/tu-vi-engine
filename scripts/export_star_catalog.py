"""Export the low-level Sao.py catalog into data/stars.json.

The low-level engine is the source of truth for star IDs/names. This utility
keeps the JSON registry reproducible without duplicating the catalog manually.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tuvi_engine" / "_engine" / "Sao.py"
TARGET = ROOT / "data" / "stars.json"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    pattern = re.compile(r"^sao\w+\s*=\s*Sao\((.+)\)$", re.MULTILINE)
    stars = []
    for raw in pattern.findall(text):
        try:
            values = ast.literal_eval("(" + raw + ")")
        except (SyntaxError, ValueError):
            continue
        if not values or not isinstance(values[0], int):
            continue
        stars.append({
            "id": values[0],
            "name": values[1],
            "element": values[2] if len(values) > 2 else None,
            "type": values[3] if len(values) > 3 else None,
            "position": values[4] if len(values) > 4 else None,
            "polarity": values[5] if len(values) > 5 else None,
            "vong_trang_sinh": bool(values[6]) if len(values) > 6 else False,
            "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        })
    stars.sort(key=lambda item: item["id"])
    payload = {
        "version": "2.0",
        "count": len(stars),
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "stars": stars,
    }
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"exported {len(stars)} stars -> {TARGET}")


if __name__ == "__main__":
    main()
