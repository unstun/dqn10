#!/usr/bin/env bash
# SessionStart hook — DQN10 (lite 版)
# 只输出 git 快照,不注入 bigmemory 内容(按需拉取模式)
set -euo pipefail

if [ -d .git ]; then
  echo "=== Git ==="
  git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(no branch)"
  git log --oneline -3 2>/dev/null || echo "(no commits)"
  git status --short 2>/dev/null || true
fi

exit 0
