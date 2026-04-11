#!/usr/bin/env bash
# ============================================================================
# sync-harness.sh — Harness 完整性四项检查
# ----------------------------------------------------------------------------
# 检查项:
#   1. symlink 完整性: .factory/commands → .claude/commands
#                       .factory/skills  → .claude/skills
#   2. CLAUDE.md ≡ AGENTS.md 逐行一致(硬规则 #15)
#   3. agents/droids 文件名覆盖: .claude/agents/ vs .factory/droids/
#   4. agents/droids 内容漂移: 正文(去 frontmatter)是否一致
# ----------------------------------------------------------------------------
# 用法: bash .claude/scripts/sync-harness.sh
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
    fi
fi

# ── 4. agents/droids 内容漂移检测 ─────────────────────────────────────────
echo "== 4. agents/droids 内容漂移 =="
if [ -d "$AGENTS_DIR" ] && [ -d "$DROIDS_DIR" ]; then
    DRIFT=0
    for agent_file in "$AGENTS_DIR"/*.md; do
        name=$(basename "$agent_file" .md)
        droid_file="$DROIDS_DIR/$name.md"
        [ -f "$droid_file" ] || continue

        # 剥除 YAML frontmatter(如有)后比较正文
        agent_body=$(awk 'NR==1&&/^---$/{s=1;next} s==1&&/^---$/{s=2;next} s!=1' "$agent_file")
        droid_body=$(awk 'NR==1&&/^---$/{s=1;next} s==1&&/^---$/{s=2;next} s!=1' "$droid_file")

        if [ "$agent_body" != "$droid_body" ]; then
            echo "  ⚠️  $name: agents 与 droids 正文不一致" >&2
            DRIFT=1
        fi
    done
    if [ "$DRIFT" -eq 0 ]; then
        echo "  ✅ agents 与 droids 正文一致"
    fi
else
    echo "  ⚠️  跳过(目录不存在)"
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
