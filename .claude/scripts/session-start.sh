#!/usr/bin/env bash
# ============================================================================
# SessionStart hook — DQN10
# ----------------------------------------------------------------------------
# 每次会话启动时输出：
#   1. 最近 5 条 git commit（项目进度）
#   2. git 分支 + status（工作区快照）
#   3. .pipeline/agent_handoff.md 最后一条 Handoff 块（跨会话交接）
#   4. .pipeline/tasks.json 中最高优先级 todo 任务（提示本次该做什么）
#
# 合并来源：
#   - 机器狗RL/.claude/scripts/session-start.sh（handoff tail）
#   - DQN9 全局 SessionStart hook（git log + status）
#
# Bug #10373: 全新会话中 stdout 可能被丢弃；/compact /clear --resume 正常
# 来源: https://code.claude.com/docs/en/hooks
# ============================================================================

set -euo pipefail

PROJECT_TRUTH=".pipeline/project_truth.md"
HANDOFF=".pipeline/agent_handoff.md"
TASKS=".pipeline/tasks.json"

# --- 1. Git 快照 -----------------------------------------------------------
if [ -d .git ]; then
  echo "=== Recent Commits ==="
  git log --oneline -5 2>/dev/null || echo "(no commits yet)"
  echo "=== Branch ==="
  git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(no branch)"
  echo "=== Status ==="
  git status --short 2>/dev/null || true
fi

# --- 2. .pipeline 检查 -----------------------------------------------------
if [ ! -f "$PROJECT_TRUTH" ]; then
  echo "⚠️  新项目，请按 CLAUDE.md 中的首次初始化步骤操作。"
  exit 0
fi

# --- 3. Handoff tail -------------------------------------------------------
if [ -f "$HANDOFF" ]; then
  LAST_LINE=$(grep -n "^## Handoff:" "$HANDOFF" | tail -1 | cut -d: -f1 || echo "")
  if [ -n "$LAST_LINE" ]; then
    echo "=== 上次交接 ==="
    tail -n +"$LAST_LINE" "$HANDOFF" | head -10
  else
    echo "📋 agent_handoff.md 存在但未找到 Handoff 条目。"
  fi
else
  echo "📋 项目已初始化但无交接记录。"
fi

# --- 4. Top todo 任务 ------------------------------------------------------
if [ -f "$TASKS" ]; then
  if command -v jq &>/dev/null; then
    TOP=$(jq -r '[.tasks[]? | select(.status=="todo")] | sort_by(.priority) | .[0] // empty | "[\(.priority // "?")] \(.title // "(untitled)")"' "$TASKS" 2>/dev/null || echo "")
    if [ -n "$TOP" ]; then
      echo "=== 下一个任务 ==="
      echo "$TOP"
    fi
  fi
fi

exit 0
