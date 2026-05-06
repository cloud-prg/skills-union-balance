#!/usr/bin/env bash
set -euo pipefail

python3 scripts/unify_skills.py \
  --dirs \
  "/Users/cloud_prg/.claude/skills" \
  "/Users/cloud_prg/.codex/skills" \
  "/Users/cloud_prg/.agents/skills" \
  "/Users/cloud_prg/.cursor/skills-cursor" \
  "/Users/cloud_prg/.cursor/plugins/cache/cursor-public/superpowers/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/skills" \
  --mode copy \
  --dry-run
