---
id: memory-retrieval
name: memory-retrieval
version: 1.0.0
description: |-
  会话启动记忆检索。Dr Sun 第一句话后自动触发,通过 auggie 从 bigmemory/ 和
  .pipeline/ 语义检索相关项目上下文,替代全文读取模式。
stages: ["all"]
tools: ["mcp__augment-context-engine__codebase-retrieval", "Task", "Read", "Grep", "Glob"]
summary: |-
  会话启动记忆检索 skill。Dr Sun 第一句话后自动触发,派 subagent 通过 auggie
  语义检索 bigmemory/ 和 .pipeline/,返回精选上下文给主会话。
  替代旧 memory-worker 全文读取模式。
primaryIntent: memory
intents: ["memory", "context-retrieval"]
capabilities: ["search-retrieval", "agent-workflow"]
domains: ["infrastructure"]
keywords: ["memory", "bigmemory", "retrieval", "context", "session-start", "auggie", "augment"]
source: custom
status: active
resourceFlags:
  hasReferences: false
  hasScripts: false
  hasTemplates: false
  hasAssets: false
  referenceCount: 0
  scriptCount: 0
  templateCount: 0
  assetCount: 0
  optionalScripts: false
---

# memory-retrieval

## Canonical Summary

会话启动记忆检索。Dr Sun 第一句话后自动触发,通过 auggie (Augment Context Engine)
从 bigmemory/ 和 .pipeline/ 语义检索与当前查询相关的项目上下文。

## Trigger Rules

本 skill 由 CLAUDE.md 硬规则 #5 触发,不依赖用户请求匹配:
- Dr Sun 发出第一句话后,主 AI **必须立即**执行本 skill
- 不等用户要求,不需要用户提及"记忆"或"上下文"

## Resource Use Rules

- 本 skill 无附带资源目录
- 依赖外部 MCP: auggie (Augment Context Engine)
- auggie 的 MCP tool 名: `mcp__augment-context-engine__codebase-retrieval`

## Execution Contract

- auggie 不可用时,回退到 Grep + Read 手动检索(见下方回退策略)
- 不修改任何 bigmemory 或 .pipeline 文件(纯只读)
- 返回的上下文控制在 800 字以内,避免污染主会话上下文窗口
- 不向 Dr Sun 展示检索过程,只在回复中自然引用相关上下文

## Upstream Instructions

### 概述

本 skill 替代旧的 memory-worker(全文读取模式)。

旧模式: 读所有文件 → LLM 总结 → 返回摘要
新模式: 提取意图 → auggie 语义检索 → 精准返回相关片段

### 执行流程

#### Step 1: 提取查询意图

从 Dr Sun 的第一句话中提取查询意图,重构为适合检索的语句。

| 用户说的 | 重构为检索查询 |
|----------|---------------|
| "继续昨天的实验" | "最近的实验进展、未完成任务和实验设计决策" |
| "写论文第四章" | "论文第四章相关的实验数据、写作进展和决策" |
| "CNN 消融实验分析" | "CNN DQN DDQN 消融实验数据、结论和未关闭问题" |
| 模糊/闲聊 | "当前项目状态、活跃任务和最近进展" |

#### Step 2: 派 subagent 执行检索

启动一个 **sonnet** 级别的 subagent(read-only),传入下方
「Subagent Prompt」及 Step 1 产出的查询意图。

**subagent 负责三件事:**
1. **路由** — 判断查询是否需要检索(会话开始默认为"需要")
2. **检索** — 调 auggie 搜索 bigmemory/ 和 .pipeline/
3. **筛选** — 过滤无关结果,只保留与查询意图匹配的内容

#### Step 3: 接收结果并开始工作

subagent 返回后,主 AI 将检索到的上下文作为背景知识,
以 "Dr Sun," 开头回复用户的实际请求。

---

### Subagent Prompt

以下为传给 subagent 的完整 prompt。
主 AI 将 `{query_intent}` 和 `{project_path}` 替换为实际值后传入。

```
你是 DQN10 项目的记忆检索 Agent。

# ── 输入 ──────────────────────────────────────────────
查询意图: {query_intent}
项目路径: {project_path}

# ── 任务 ──────────────────────────────────────────────
从项目知识库(bigmemory/ 和 .pipeline/)中检索与查询意图相关的信息。

# ── 检索策略 ──────────────────────────────────────────

## 主路径: auggie 语义检索

调用 mcp__augment-context-engine__codebase-retrieval:
  information_request: 在 bigmemory 和 .pipeline 知识库中查找: {query_intent}
  directory_path: {project_path}

要点:
- 在 information_request 中明确提及 "bigmemory" 和 ".pipeline"
  以引导 auggie 优先搜索这些目录
- 如果首次结果不够,换一组关键词再调一次(最多 2 次)

## 补充: 热区兜底

无论 auggie 返回什么,始终补充读取:
  bigmemory/热区/状态简报.md

原因: 状态简报包含当前活跃任务和关键上下文,
是每次会话都需要的基线信息。

## 回退: auggie 不可用时

如果 auggie 报错或超时,切换到手动检索:
1. Read bigmemory/热区/ 全部 3 个文件
2. Grep bigmemory/冷区/ 搜索查询关键词
3. Grep .pipeline/ 搜索查询关键词

# ── 结果筛选 ──────────────────────────────────────────

对 auggie 返回的结果进行相关性判断:
- ✅ 保留: 与查询意图直接相关的 bigmemory/冷区 记录
- ✅ 保留: .pipeline/ 中相关的实验/综述/术语/文献条目
- ✅ 保留: 热区中的状态/决策/改动信息
- ❌ 丢弃: 代码文件(Python/Shell 等 — 代码检索由 auggie 常规功能负责)
- ❌ 丢弃: CLAUDE.md / AGENTS.md / .claude/rules/ (已在 system prompt 中)
- ❌ 丢弃: 与查询无关的文件内容

# ── 输出格式 ──────────────────────────────────────────

严格按以下格式输出,总字数 ≤ 800:

---
## 项目记忆上下文

### 当前状态
[从状态简报提取: 活跃任务、关键进展、环境约束]

### 相关记录
[从冷区/.pipeline 检索到的相关条目]
[每条标注来源: (文件路径)]

### 未关闭决策
[与本次查询相关的未关闭决策,如有]

### 来源文件
- [引用的文件路径列表]
---

# ── 约束 ──────────────────────────────────────────────
- 只返回与查询直接相关的信息,不要全文转发
- 标注信息来源(文件路径)
- 如果没找到相关信息,明确说"未找到相关记忆",不要编造
- 中文输出
- 总字数 ≤ 800
```

---

### 回退策略总结

| 场景 | 行为 |
|------|------|
| auggie 正常 | auggie 检索 + 热区兜底 |
| auggie 返回结果不足 | 换关键词重试一次 + 热区兜底 |
| auggie 报错/超时 | Read 热区 + Grep 冷区和 .pipeline |
| subagent 整体失败 | 主 AI 自行 Read 热区 3 个文件(最低保障) |

### 与旧 memory-worker 的对比

| 维度 | 旧 memory-worker | 本 skill |
|------|-------------------|----------|
| 检索方式 | 读全文 → LLM 总结 | auggie 语义检索 → 精准返回 |
| 覆盖范围 | bigmemory/ 为主 | bigmemory/ + .pipeline/ 全覆盖 |
| 精准度 | 依赖 LLM 总结能力,文件多时遗漏 | 依赖 auggie 嵌入模型,语义匹配 |
| 回退 | 无 | 三级回退(重试 → 手动 → 热区兜底) |
| 延迟 | 10-20s(读文件+总结) | 15-30s(subagent+auggie) |
| 可复用 | 仅限特定平台 | 任何能调 auggie 的 Agent |

### 迁移状态

配套修改已于 2026-04-11 完成:
- CLAUDE.md / AGENTS.md 硬规则 #5 + 记忆系统段落 — 已更新
- `.claude/rules/memory-system.md` — 已更新
- `.factory/droids/memory-worker.md` — 已标记 deprecated
