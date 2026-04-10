# CLAUDE.md 维护规范

基于 `.pipeline/survey/claude-md-optimization.md` 的 28 条实证发现,维护 CLAUDE.md 及 rules/ 时须遵循以下标准。

## 注入机制

- CLAUDE.md 以 user message 注入(非 system prompt),Claude 逐条判断相关性,不相关的规则会被静默跳过。
- `.claude/rules/*.md` 无 `paths` 则每次会话全量加载;有 `paths` 则仅在读取匹配文件时注入。
- 指令预算约 150-200 条(含系统 prompt ~50 条),根文件目标 ≤100 行。

## 写作原则

- **正面框架优于负面**:MUST 优于 NEVER。负面指令需先处理被禁行为才能抑制(粉色大象效应)。NEVER 占比应 <10%。
- **附加理由(Why)**:帮助 AI 判断边界情况。"每次会话只做一件事。Why: 避免漂移串任务"比单纯禁令更有效。
- **IMPORTANT/YOU MUST 有效但滥用稀释效果**:仅用于真正关键的规则。
- **重复规则 3 次不提升遵从率**:CLAUDE.md 是 advisory 级别,重复无用。
- **首尾偏差(U-shaped)**:文件中间位置的指令遵循概率最低,最重要的规则放首尾。

## 内容取舍

**有效内容**(应保留):
- 非显而易见的工具决策(如"用 ACE 不用 grep")
- 非常规配置和项目特有约束
- AI 反复犯错的规则(当测试套件用)

**无效内容**(应删除或外置):
- 目录结构/架构概述 — agent 善于自发现,静态描述浪费 token
- 叙事性背景段落 — 代码任务中被相关性过滤器降权
- 过时的结构描述 — 代码变了但描述没更新时变成负担
- 频繁变动的信息 — 嵌入后变成过时负担
- linter 可执行的代码风格规则 — "Never send an LLM to do a linter's job"
- LLM 生成的指令内容 — 实证降低性能 + 增加成本

## Advisory vs Deterministic

- CLAUDE.md 是 advisory(Claude 尝试遵守),hooks 是 deterministic(确定性执行不可跳过)。
- 必须零例外执行的机械性规则应 hook 化,不要放在 CLAUDE.md 里期望 AI 永远记住。

## 诊断

- 规则反复被违反 → 文件太长,规则被噪音淹没
- Claude 问 CLAUDE.md 中已有答案的问题 → 措辞模糊
- 同一问题纠正 >2 次 → `/clear` 重启
- 把 CLAUDE.md 当测试套件 — Claude 犯错时更新,行为已正确时裁剪
