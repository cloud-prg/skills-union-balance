---
name: skill-union-balancer
description: 统一处理多个 skills 平台目录。遇到用户提到“合并 skills、取并集、目录对齐、同步 skill 到多个平台、均摊分发”时必须使用。该技能会扫描多个目录中的 SKILL.md 目录单元，取并集并把缺失 skill 分发到每个目标目录，支持 dry-run、copy 和 symlink 模式。
---

# Skill Union Balancer

用于把多个 skills 目录做统一化处理，流程是：

1. 扫描多个目录中“子目录 + `SKILL.md`”结构。
2. 取 skill 名称并集。
3. 把并集中缺失的 skill 分发到每个目录。
4. 输出执行摘要，支持先预览再落盘。

## 使用方式

优先执行 dry-run：

```bash
python3 scripts/unify_skills.py \
  --dirs "~/.claude/skills" "~/.codex/skills" "~/.agents/skills" "~/.cursor/skills-cursor" \
  --mode copy \
  --dry-run
```

确认无误后正式执行：

```bash
python3 scripts/unify_skills.py \
  --dirs "~/.claude/skills" "~/.codex/skills" "~/.agents/skills" "~/.cursor/skills-cursor" \
  --mode copy
```

## 可选参数

- `--mode copy|symlink`：复制目录或软链接。
- `--dry-run`：仅预览动作。
- `--replace-existing`：覆盖已存在目录（默认跳过已存在项）。

## 约定

- skill 的判定标准是：目录下存在 `SKILL.md`。
- 同名 skill 的来源按 `--dirs` 提供顺序优先选第一个出现的目录。
- 为了减少误覆盖，默认不替换已存在目标目录。
