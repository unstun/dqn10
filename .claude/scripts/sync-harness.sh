#!/usr/bin/env bash
# ============================================================================
# sync-harness.sh — Harness 完整性三项检查
# ----------------------------------------------------------------------------
# 检查项:
#   1. symlink 完整性: .factory/commands → .claude/commands
#                       .factory/skills  → .claude/skills
#   2. CLAUDE.md ≡ AGENTS.md 逐行一致(硬规则 #23)
#   3. agents/droids 文件名覆盖: .claude/agents/ vs .factory/droids/
# ----------------------------------------------------------------------------
# 用法: bash scripts/sync-harness.sh
# 返回: 全部通过 → exit 0; 有失败 → exit 2
# ============================================================================
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

FAIL=0

# ── 1. Symlink 完整性 ──────────────────────────────────────────────────────
check_symlink() {
    local link="$1" target="$2"
    if [ -L "$link" ]; then
        actual=$(readlink "$link")
        if [ "$actual" = "$target" ]; then
            echo "  ✅ $link → $target"
        else
            echo "  ❌ $link → $actual (期望 $target)" >&2
            FAIL=1
        fi
    else
        echo "  ❌ $link 不是 symlink" >&2
        FAIL=1
    fi
}

echo "== 1. Symlink 完整性 =="
check_symlink ".factory/commands" "../.claude/commands"
check_symlink ".factory/skills"   "../.claude/skills"

# ── 2. CLAUDE.md ≡ AGENTS.md ──────────────────────────────────────────────
echo "== 2. CLAUDE.md ≡ AGENTS.md =="
if [ ! -f "CLAUDE.md" ] || [ ! -f "AGENTS.md" ]; then
    echo "  ❌ 缺少 CLAUDE.md 或 AGENTS.md" >&2
    FAIL=1
elif diff -q "CLAUDE.md" "AGENTS.md" >/dev/null; then
    echo "  ✅ CLAUDE.md ≡ AGENTS.md"
else
    echo "  ❌ CLAUDE.md 与 AGENTS.md 不一致:" >&2
    diff --brief "CLAUDE.md" "AGENTS.md" >&2 || true
    FAIL=1
fi

# ── 3. agents/droids 文件名覆盖 ───────────────────────────────────────────
echo "== 3. agents/droids 覆盖 =="
AGENTS_DIR=".claude/agents"
DROIDS_DIR=".factory/droids"

if [ ! -d "$AGENTS_DIR" ] || [ ! -d "$DROIDS_DIR" ]; then
    echo "  ⚠️  $AGENTS_DIR 或 $DROIDS_DIR 不存在, 跳过" >&2
else
    # 提取文件名(无路径无后缀)
    agents=$(ls "$AGENTS_DIR"/*.md 2>/dev/null | xargs -I{} basename {} .md | sort)
    droids=$(ls "$DROIDS_DIR"/*.md 2>/dev/null | xargs -I{} basename {} .md | sort)

    only_agents=$(comm -23 <(echo "$agents") <(echo "$droids"))
    only_droids=$(comm -13 <(echo "$agents") <(echo "$droids"))

    if [ -z "$only_agents" ] && [ -z "$only_droids" ]; then
        echo "  ✅ agents 与 droids 文件名完全覆盖"
    else
        if [ -n "$only_agents" ]; then
            echo "  ℹ️  仅在 .claude/agents/: $only_agents"
        fi
        if [ -n "$only_droids" ]; then
            echo "  ℹ️  仅在 .factory/droids/: $only_droids"
        fi
        # 信息性输出, 不算失败(两边格式不同, 不要求完全对齐)
    fi
fi

# ── 结果 ──────────────────────────────────────────────────────────────────
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "🟢 Harness 检查全部通过"
    exit 0
else
    echo "🔴 Harness 检查有失败项" >&2
    exit 2
fi
