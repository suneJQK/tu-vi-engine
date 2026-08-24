from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tu-vi-engine-repaired.zip"
EXCLUDED_DIRS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv", "artifact"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pyd"}
EXCLUDED_FILES = {OUTPUT.name}


def should_skip(path: Path) -> bool:
    if path.name in EXCLUDED_FILES:
        return True
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True
    return path.suffix.lower() in EXCLUDED_SUFFIXES


def main() -> None:
    if OUTPUT.exists():
        OUTPUT.unlink()
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or should_skip(path):
                continue
            archive.write(path, Path("tu-vi-engine") / path.relative_to(ROOT))
    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    main()
