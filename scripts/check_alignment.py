#!/usr/bin/env python3
"""Check top-level skill-name alignment across multiple skill directories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Set


def collect_skill_names(base_dir: Path) -> Set[str]:
    names: Set[str] = set()
    if not base_dir.exists() or not base_dir.is_dir():
        return names
    for child in base_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if (child / "SKILL.md").exists():
            names.add(child.name)
    return names


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check top-level skill alignment across directories."
    )
    parser.add_argument("--dirs", nargs="+", required=True, help="Skill directories.")
    parser.add_argument(
        "--report-json",
        help="Optional output path for JSON report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dirs = [Path(p).expanduser().resolve() for p in args.dirs]

    by_dir: Dict[str, Set[str]] = {str(d): collect_skill_names(d) for d in dirs}
    union: Set[str] = set()
    for names in by_dir.values():
        union |= names

    print(f"union_top_level_count: {len(union)}")
    for d, names in by_dir.items():
        missing = sorted(union - names)
        print(f"- {d}")
        print(f"  count: {len(names)}")
        print(f"  missing: {len(missing)}")

    if args.report_json:
        report_path = Path(args.report_json).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "union_top_level_count": len(union),
            "directories": [
                {
                    "path": d,
                    "count": len(names),
                    "missing_count": len(union - names),
                    "missing": sorted(union - names),
                }
                for d, names in by_dir.items()
            ],
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[INFO] report written: {report_path}")


if __name__ == "__main__":
    main()
