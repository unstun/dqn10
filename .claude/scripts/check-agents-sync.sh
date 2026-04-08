#!/usr/bin/env bash
# ============================================================================
# check-agents-sync.sh — 校验 CLAUDE.md 与 AGENTS.md 逐行一致(硬规则 #22)
# ----------------------------------------------------------------------------
# 用法:`bash .claude/scripts/check-agents-sync.sh`
# 返回:一致 → exit 0;不一致 → 打印 diff 并 exit 2
# ============================================================================
set -euo pipefail

A="CLAUDE.md"
B="AGENTS.md"

if [ ! -f "$A" ] || [ ! -f "$B" ]; then
  echo "❌ 缺少 $A 或 $B" >&2
  exit 2
fi

if diff -q "$A" "$B" >/dev/null; then
  echo "✅ CLAUDE.md ≡ AGENTS.md"
  exit 0
else
  echo "❌ CLAUDE.md 与 AGENTS.md 不一致:" >&2
  diff "$A" "$B" >&2 || true
  exit 2
fi
