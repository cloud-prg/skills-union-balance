#!/usr/bin/env python3
"""Unify skills from multiple directories by union + distribution."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class SkillSource:
    name: str
    source_dir: Path
    skill_path: Path


def discover_skills(base_dirs: Iterable[Path]) -> Dict[str, SkillSource]:
    union: Dict[str, SkillSource] = {}
    for base_dir in base_dirs:
        if not base_dir.exists():
            print(f"[WARN] Missing directory: {base_dir}")
            continue
        if not base_dir.is_dir():
            print(f"[WARN] Not a directory: {base_dir}")
            continue

        for child in sorted(base_dir.iterdir()):
            if not child.is_dir():
                continue
            if not (child / "SKILL.md").exists():
                continue
            if child.name not in union:
                union[child.name] = SkillSource(
                    name=child.name,
                    source_dir=base_dir,
                    skill_path=child,
                )
    return union


def copy_skill(src: Path, dst: Path, replace_existing: bool) -> str:
    if dst.exists():
        if not replace_existing:
            return "skip_exists"
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return "copied"


def link_skill(src: Path, dst: Path, replace_existing: bool) -> str:
    if dst.exists():
        if not replace_existing:
            return "skip_exists"
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    dst.symlink_to(src, target_is_directory=True)
    return "linked"


def apply_distribution(
    base_dirs: List[Path],
    union: Dict[str, SkillSource],
    mode: str,
    dry_run: bool,
    replace_existing: bool,
    continue_on_error: bool,
    report_json: Path | None,
) -> None:
    copied = 0
    linked = 0
    skipped = 0
    warnings: List[str] = []
    errors: List[Dict[str, str]] = []
    per_target: Dict[str, Dict[str, int]] = {}

    for target_dir in base_dirs:
        target_key = str(target_dir)
        per_target[target_key] = {
            "would_copy": 0,
            "would_link": 0,
            "would_skip_exists": 0,
            "copied": 0,
            "linked": 0,
            "skip_exists": 0,
        }
        if not target_dir.exists():
            warn_msg = f"Skip missing target dir: {target_dir}"
            warnings.append(warn_msg)
            print(f"[WARN] {warn_msg}")
            continue
        for skill_name, source in sorted(union.items()):
            target_path = target_dir / skill_name
            src_path = source.skill_path

            if dry_run:
                action = "would_copy" if mode == "copy" else "would_link"
                if target_path.exists() and not replace_existing:
                    action = "would_skip_exists"
                per_target[target_key][action] += 1
                print(
                    f"[DRY] {action}: {skill_name} | src={src_path} -> dst={target_path}"
                )
                continue

            if mode == "copy":
                try:
                    result = copy_skill(src_path, target_path, replace_existing)
                    if result == "copied":
                        copied += 1
                        per_target[target_key]["copied"] += 1
                    else:
                        skipped += 1
                        per_target[target_key]["skip_exists"] += 1
                except Exception as exc:
                    err_msg = str(exc)
                    errors.append(
                        {
                            "target_dir": target_key,
                            "skill_name": skill_name,
                            "source_path": str(src_path),
                            "target_path": str(target_path),
                            "error": err_msg,
                        }
                    )
                    print(f"[ERR] failed copy: {skill_name} -> {target_path} | {err_msg}")
                    if not continue_on_error:
                        raise
                    continue
            else:
                try:
                    result = link_skill(src_path, target_path, replace_existing)
                    if result == "linked":
                        linked += 1
                        per_target[target_key]["linked"] += 1
                    else:
                        skipped += 1
                        per_target[target_key]["skip_exists"] += 1
                except Exception as exc:
                    err_msg = str(exc)
                    errors.append(
                        {
                            "target_dir": target_key,
                            "skill_name": skill_name,
                            "source_path": str(src_path),
                            "target_path": str(target_path),
                            "error": err_msg,
                        }
                    )
                    print(f"[ERR] failed link: {skill_name} -> {target_path} | {err_msg}")
                    if not continue_on_error:
                        raise
                    continue

            print(f"[OK] {result}: {skill_name} -> {target_path}")

    if not dry_run:
        print("\n=== Summary ===")
        print(f"skills_union_count: {len(union)}")
        print(f"copied: {copied}")
        print(f"linked: {linked}")
        print(f"skipped: {skipped}")
        print(f"errors: {len(errors)}")

    if report_json is not None:
        report_json.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "dry_run": dry_run,
            "replace_existing": replace_existing,
            "skills_union_count": len(union),
            "skills_union": sorted(union.keys()),
            "warnings": warnings,
            "errors": errors,
            "totals": {
                "copied": copied,
                "linked": linked,
                "skipped": skipped,
                "errors": len(errors),
            },
            "per_target": per_target,
        }
        report_json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[INFO] report written: {report_json}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Unify skills by union across directories and distribute to every directory."
        )
    )
    parser.add_argument(
        "--dirs",
        nargs="+",
        required=True,
        help="Skill directories to process (e.g. ~/.claude/skills ~/.codex/skills).",
    )
    parser.add_argument(
        "--mode",
        choices=("copy", "symlink"),
        default="copy",
        help="Distribution mode: copy folders or create symlinks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without writing files.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing target skill folders/files.",
    )
    parser.add_argument(
        "--report-json",
        help="Write execution report JSON to this file path.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep distributing to other skills/directories even if some copies fail.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dirs = [Path(p).expanduser().resolve() for p in args.dirs]
    union = discover_skills(base_dirs)

    print(f"Discovered union skills: {len(union)}")
    for name, source in sorted(union.items()):
        print(f"- {name} (from {source.source_dir})")

    apply_distribution(
        base_dirs=base_dirs,
        union=union,
        mode=args.mode,
        dry_run=args.dry_run,
        replace_existing=args.replace_existing,
        continue_on_error=args.continue_on_error,
        report_json=Path(args.report_json).expanduser().resolve()
        if args.report_json
        else None,
    )


if __name__ == "__main__":
    main()
