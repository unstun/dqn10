# PreCompact Hook 最佳实践调研

> 调研日期：2026-04-08
> 调研者：DQN10 worker session
> 任务来源：`.pipeline/tasks.json#research-precompact-hook`
> 触发动机：第一版 DQN10 只有 `Stop` hook 拦 handoff 落盘；`/compact` 触发的自动压缩可能在 Stop hook 介入前就把交接笔记的写入机会吃掉，导致下次会话失忆。

---

## TL;DR（先看结论）

1. **PreCompact hook 真实存在**，matcher 支持 `manual` / `auto` / `*`，输入含 `trigger` + `custom_instructions`。
2. **PreCompact 不能 block compaction**——官方文档原文："PreCompact, PostCompact … cannot block or modify notifications. … No decision control. Used for side effects like logging or cleanup"。exit code 2 只把 stderr 显示给用户，**不阻断**。
3. **存在已知严重缺陷**：anthropics/claude-code#13572 多名用户（含 v2.1.7 macOS jeffc-dev、Linux mputz）报告 PreCompact hook 在 manual `/compact` **完全不触发**。issue 已 CLOSED 但属"inactive 自动关闭"，**未见修复说明**。
4. **DQN10 落地建议**：**双轨方案**——
   - **轨 A（必装）**：装一个 PreCompact hook，把"读 transcript → 提炼 → 写 `agent_handoff.md`"的脚本接上。即使 manual `/compact` 不触发，auto-compact 触发它就赚了。
   - **轨 B（必装）**：把 EmanuelFaria 的 "custom `/compact` instructions" workaround 编成一个 `.claude/commands/compact.md` slash command 别名，**强制 Dr Sun 用 `/compact-safe`（而不是裸 `/compact`）**，让 Claude 自己在压缩时把 handoff 落盘。
   - **轨 C（不推荐）**：who96 那种"PreCompact 写文件 + 外部 supervisor 把 `/compact` 改写成 `/clear`"——多了一个 supervisor 进程，DQN10 不需要这种复杂度。
5. **不要指望 PreCompact 单独解决问题**。它是"加固"，不是"防线"。

---

## 一、PreCompact hook 官方事实（来自 docs）

来源：<https://code.claude.com/docs/en/hooks>

### 1.1 Schema

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "hook_event_name": "PreCompact",
  "trigger": "manual" | "auto",
  "custom_instructions": "<string>"
}
```

- `trigger="manual"`：用户运行 `/compact [instructions]`，`custom_instructions` = 用户传入的指令
- `trigger="auto"`：Claude Code 自动压缩（context 接近上限），`custom_instructions` 为空字符串
- `transcript_path` 指向当前会话的 jsonl，hook 脚本可以读它做摘要

### 1.2 Matcher

```json
{
  "PreCompact": [
    {
      "matcher": "*",
      "hooks": [{ "type": "command", "command": "bash .claude/scripts/pre-compact.sh" }]
    }
  ]
}
```

`matcher` 可填 `manual` / `auto` / `*`。

### 1.3 阻断能力（重要）

| Hook event | 能 block？| exit 2 行为 |
|---|---|---|
| `Stop` | **能** | 阻止 Claude 停止，强制继续对话 |
| `PreCompact` | **不能** | 仅把 stderr 显示给用户，compaction 照常进行 |

官方原文："PreCompact, PostCompact … cannot block or modify notifications. … No decision control. Used for side effects like logging or cleanup."

**结论**：PreCompact 只能"在压缩前做事"，不能"阻止压缩"。

---

## 二、严重缺陷：anthropics/claude-code#13572

来源：<https://github.com/anthropics/claude-code/issues/13572>

### 2.1 问题
PreCompact hook 配置无误（`/hook:status` 显示已注册、脚本可执行、手工调用正常），但 `/compact` 命令运行时 **hook 不被调用**。多人复现：

- mputz（issue 作者，2025-12-10，Linux）：手工 `/compact` 不触发，auto 触发的也没看到
- jeffc-dev（2026-01-14，macOS v2.1.7）："Claude Code's PreCompact hook never fires for me, either for manual or auto. The Stop hook fires after compact completes, but PreCompact does not fire before"
- rpolitex（2025-12-26，v2.0.76）：项目级 hook 正常，只有 Plugin 级 hook 有问题

### 2.2 状态
- 创建：2025-12-10
- 关闭：2026-02-27（github-actions bot："Closing for now — inactive for too long"）
- **未见修复 commit / changelog 引用**。属于自动归档，不代表已修复。
- 锁定：2026-03-07（自动锁定）

### 2.3 含义
**不能假定 PreCompact 一定会触发**。设计方案必须容忍它静默失效。

---

## 三、社区方案对比

### 方案 A：PreCompact 写 handoff（who96 模式）

来源：<https://github.com/who96/claude-code-context-handoff>

**机制**：
1. PreCompact 触发 → bash 脚本读 `transcript_path` 的 jsonl → 提炼最近 N 条用户消息 + 助手代码片段 + 文件路径 → 写 `~/.claude/handoff/<session_id>.md`
2. SessionStart(compact) 触发 → 读取 handoff → 通过 `additionalContext` 字段注入新会话上下文
3. 因为 `/compact` 不可被 hook 改写（官方限制），who96 还配了一个外部 supervisor 进程把 `/compact` 改写成 `/clear` 来"绕道"——**这个 supervisor 是 DQN10 不需要的复杂度**

**优点**：
- 自动化高，用户无感
- handoff 是真实的 transcript 内容，不依赖 LLM 自我总结

**缺点**：
- 受 #13572 影响，manual `/compact` 不触发就白搭
- supervisor 进程是额外维护负担
- 提炼逻辑（"最近 15 条用户消息"）跟 DQN10 的 `## Handoff:` 块格式不兼容，要重写脚本

### 方案 B：custom `/compact` instructions（EmanuelFaria 模式）

来源：anthropics/claude-code#13572 评论 by EmanuelFaria，3 次实测成功

**机制**：
利用一个被低估的事实：**`/compact <instructions>` 的 `<instructions>` 会被插入到压缩 prompt 里**，让总结 LLM 强制按你的格式输出。

EmanuelFaria 的指令模板示例：
```
/compact In addition to the default summary, explicitly include these sections at the END:

0) COMPACT NUMBER - This is compact #[N]
1) IMMEDIATE NEXT ACTION - [Specific imperative with file paths]
2) SETTLED DECISIONS - ...
3) DEAD ENDS - What failed and WHY
4) TRUST ANCHORS - What's verified working
5) USER PREFERENCES - ...
6) TASK QUEUE - ...
7) BREAKTHROUGHS - ...
```

EmanuelFaria 把它包成了一个 `/precompact` slash command，让 Claude 先分析当前会话再生成对应的 `/compact ...` 指令，Dr Sun 一行命令就能用。

**优点**：
- **完全绕开 #13572**——不依赖 hook
- 0 基础设施，只是一个 markdown 文件
- 让 Claude 自己当"提取引擎"，比正则脚本提炼准
- DQN10 可以直接照搬：把 7 个 section 改成 DQN10 的 handoff 5 段式（**已完成**/**未完成**/**未改动**/**下一会话首动作**/+CLAUDE.md 引用）

**缺点**：
- 只对 manual `/compact` 有效。auto-compact 触发时没机会插指令。
- 依赖人类记得用 `/compact-safe` 而不是裸 `/compact`

### 方案 C：纯 Stop hook 加强（不上 PreCompact）

**机制**：
继续用现有 `stop-check.sh`，但缩短 `MAX_AGE`（比如 60s），强制 Claude 每次回复结束都更新 handoff。

**优点**：
- 0 新代码
- 已知工作

**缺点**：
- 不解决"compaction 在 Stop 之前发生"的核心问题
- 容易引发"为了过 hook 而塞水分到 handoff"的反模式（Dr Sun 会觉得吵）

### 方案 D：PreCompact + 自定义 instructions 双轨（推荐）

**机制 = A + B 的简化组合**：

1. **轨 A**（防 auto-compact）：装 `pre-compact.sh`
   - 读 stdin 的 `trigger` 字段
   - 如果 `agent_handoff.md` 的 mtime > 60s（即"近期没更新"），就追加一条占位 handoff（说明触发原因是 auto-compact、当前 cwd、session_id）
   - exit 0（不阻断 compaction）
   - 因为 #13572 这个 hook 在 manual `/compact` 时可能不触发——但 auto-compact 是设计上更危险的场景（用户没准备），有它就好得多

2. **轨 B**（防 manual /compact）：装 `.claude/commands/compact-safe.md`
   - 一个 slash command，内容是"分析当前会话，生成包含 DQN10 5 段式 handoff 的 `/compact ...` 指令并执行"
   - 在 CLAUDE.md 的 "Compact 须知" 段加一句：**永远用 `/compact-safe`，不要裸 `/compact`**

**优点**：
- 两条独立防线，任一条工作都能保住 handoff
- 不引入 supervisor 进程
- 跟现有 Stop hook 不冲突（Stop hook 仍然防"忘了写就结束"，PreCompact 防"没机会写就被 compact"）

**缺点**：
- 需要新建 2 个文件（hook + slash command）
- slash command 部分需要 Dr Sun 配合用 `/compact-safe`

---

## 四、对 DQN10 的具体建议

### 4.1 是否落地？
**是**。但优先级 **medium**，不是 high。理由：
- 当前 Stop hook 已经能拦"忘记写就 stop"的 99% 情况
- compaction 漏网概率取决于 Dr Sun 的 session 长度——目前 DQN10 工作流多是单任务短会话，命中概率不高
- 但一旦命中，成本是"下次会话失忆 + handoff 链断"，损失大
- 两个文件的工作量对得起这个保险

### 4.2 落地方式：方案 D
新建 2 个文件 + 改 2 个文件：

**新建**：
1. `.claude/scripts/pre-compact.sh`（轨 A）
2. `.claude/commands/compact-safe.md`（轨 B）

**修改**：
1. `.claude/settings.json`：在 `hooks` 里加 `PreCompact` 段
2. `CLAUDE.md` + `AGENTS.md`："Compact 须知"段加一句"用 `/compact-safe`，不裸 `/compact`"，并跑 `check-agents-sync.sh` 验证

### 4.3 不做的事
- ❌ 不上 who96 supervisor（多余复杂度）
- ❌ 不缩短 Stop hook 的 `MAX_AGE`（会逼自己塞水分 handoff）
- ❌ 不依赖 PreCompact 单独工作（#13572 风险）

### 4.4 预期效果
- auto-compact 命中：PreCompact 触发 → 占位 handoff 落盘 → 下次会话至少知道"是被 auto-compact 中断的"和"中断时的 cwd / session_id"
- manual compact 命中：Dr Sun 用 `/compact-safe` → 在 compaction prompt 里强制 LLM 按 5 段式输出 → handoff 内容直接进新会话上下文
- 都没命中（Dr Sun 裸 `/compact` 又赶上 #13572）：退化到现有 Stop hook 兜底

---

## 五、参考资料

### 官方文档
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks)（PreCompact 段、exit code 2 行为表）
- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)

### 社区
- [anthropics/claude-code#13572](https://github.com/anthropics/claude-code/issues/13572) — PreCompact hook not triggered when /compact runs（含 EmanuelFaria 的 custom-instructions workaround）
- [anthropics/claude-code#15923](https://github.com/anthropics/claude-code/issues/15923) — Feature request: pre-compaction hook for context preservation
- [who96/claude-code-context-handoff](https://github.com/who96/claude-code-context-handoff) — 完整参考实现（含 supervisor）
- [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) — hook 配置范例库
- [Yuanchang's blog: Auto Memory & PreCompact Hooks Explained](https://yuanchang.org/en/posts/claude-code-auto-memory-and-hooks/)
- [Code Coup: Context Recovery Hook for Claude Code](https://medium.com/coding-nexus/context-recovery-hook-for-claude-code-never-lose-work-to-compaction-7ee56261ee8f)（2026-02 Medium 文章）

---

## 六、未解决的问题（留给后续）

1. **#13572 在最新版 Claude Code（2026-04 当前版本）是否已修复？** 调研时未读最新 changelog。落地前应做 `claude --version` 确认 + 跑一次 manual `/compact` 测试 PreCompact 是否触发。
2. **`SessionStart(compact|clear)` matcher 注入 `additionalContext` 的具体语法**？who96 用了，但本笔记没读细。如果要做"自动注入 handoff 到新会话"（比 Dr Sun 手动读 handoff 更省事），需要补查这一段。
3. **transcript_path 的 jsonl 结构**？如果将来 PreCompact 脚本要从 transcript 提炼内容（而不是只写占位 handoff），得先 reverse-engineer 这个 jsonl 的结构。
