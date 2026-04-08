#!/usr/bin/env bash
# Stop hook: 强制 handoff 写入
# exit 0 = 放行, exit 2 = block（继续对话）
# 来源: https://code.claude.com/docs/en/hooks
# 防循环: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

HANDOFF=".pipeline/agent_handoff.md"
MAX_AGE=300  # 秒

# 从 stdin 读取 JSON
INPUT=$(cat)

# 解析 stop_hook_active（优先 jq，降级 python3）
if command -v jq &>/dev/null; then
  ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
else
  ACTIVE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('stop_hook_active',False)).lower())" 2>/dev/null || echo "false")
fi

# 防无限循环：如果已在强制继续状态，直接放行
if [ "$ACTIVE" = "true" ]; then
  exit 0
fi

# 检查 handoff 文件是否存在
if [ ! -f "$HANDOFF" ]; then
  echo "❌ agent_handoff.md 不存在。请先写交接笔记再结束。" >&2
  exit 2
fi

# 检查文件是否在最近 N 秒内被修改
if [[ "$(uname)" == "Darwin" ]]; then
  MTIME=$(stat -f %m "$HANDOFF")
else
  MTIME=$(stat -c %Y "$HANDOFF")
fi
NOW=$(date +%s)
AGE=$((NOW - MTIME))

if [ "$AGE" -gt "$MAX_AGE" ]; then
  echo "❌ agent_handoff.md 超过 ${MAX_AGE} 秒未更新。请追加本次交接笔记再结束。" >&2
  exit 2
fi

exit 0
