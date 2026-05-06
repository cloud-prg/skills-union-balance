#!/usr/bin/env python3
"""Unify skills from multiple directories by union + distribution."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
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
) -> None:
    copied = 0
    linked = 0
    skipped = 0

    for target_dir in base_dirs:
        if not target_dir.exists():
            print(f"[WARN] Skip missing target dir: {target_dir}")
            continue
        for skill_name, source in sorted(union.items()):
            target_path = target_dir / skill_name
            src_path = source.skill_path

            if dry_run:
                action = "would_copy" if mode == "copy" else "would_link"
                if target_path.exists() and not replace_existing:
                    action = "would_skip_exists"
                print(
                    f"[DRY] {action}: {skill_name} | src={src_path} -> dst={target_path}"
                )
                continue

            if mode == "copy":
                result = copy_skill(src_path, target_path, replace_existing)
                if result == "copied":
                    copied += 1
                else:
                    skipped += 1
            else:
                result = link_skill(src_path, target_path, replace_existing)
                if result == "linked":
                    linked += 1
                else:
                    skipped += 1

            print(f"[OK] {result}: {skill_name} -> {target_path}")

    if not dry_run:
        print("\n=== Summary ===")
        print(f"skills_union_count: {len(union)}")
        print(f"copied: {copied}")
        print(f"linked: {linked}")
        print(f"skipped: {skipped}")


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
    )


if __name__ == "__main__":
    main()
