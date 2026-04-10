# CLAUDE.md 优化技巧调研
> 创建：2026-04-09 | 最后更新：2026-04-09

## 背景
DQN10 的 CLAUDE.md 约 192 行、36 条硬规则，已触及官方推荐的 200 行上限。
需调研优化技巧以提升 AI 遵从率、减少 token 浪费、提高可维护性。

## 关键发现

### 一、注入机制与性能约束

1. **CLAUDE.md 以 user message 注入**（非 system prompt），附带"IMPORTANT: this context may or may not be relevant"disclaimer。Claude 逐条判断相关性,不相关的规则会被静默跳过（来源：[官方 memory 文档](https://code.claude.com/docs/en/memory)、[HumanLayer 博客](https://www.humanlayer.dev/blog/writing-a-good-claude-md)）✅ 已验证

2. **指令预算约 150-200 条**，Claude Code 系统 prompt 已占 ~50 条。来源是第三方博客估算,非 Anthropic 官方数据,但被广泛引用（来源：[HumanLayer 博客](https://www.humanlayer.dev/blog/writing-a-good-claude-md)）⚠️ 第三方估算

3. **官方建议 < 200 行 per file**，原文："target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."（来源：[官方 memory 文档](https://code.claude.com/docs/en/memory)）⚠️ 官方 memory 页有此数字,best-practices 页用定性描述

4. **首尾偏差（U-shaped performance curve）**：中间位置的指令被遵循概率最低。学术来源：Liu et al. 2023 "Lost in the Middle: How Language Models Use Long Contexts"（来源：[arXiv:2307.03172](https://arxiv.org/abs/2307.03172)）✅ 已验证

### 二、ETH Zurich 实证研究 (arXiv:2602.11988, 2026-02)

5. **人工编写指令文件：+4% 准确率**（AGENTbench 上）✅ 已验证
6. **LLM 生成指令文件：-0.5% (SWE-bench Lite) 到 -2% (AGENTbench)**，5/8 设置中降低成功率 ✅ 已验证
7. **推理成本增加：LLM 生成 +20-23%，人工编写 ~19%** ✅ 已验证
8. **目录结构/架构概述不减少 agent 导航时间**——agent 善于自发现，静态描述浪费 token ✅ 已验证
9. **真正有用的内容**：非显而易见的工具决策（如"用 uv 不用 pip"）、非常规 CI 配置、项目特有约束 ✅ 已验证

### 三、规则措辞

10. **正面框架（MUST）优于负面（NEVER）**——"粉色大象效应"（ironic process theory），负面指令需先处理被禁止的行为才能抑制。NEVER 应控制在 < 10%（来源：[16x Engineer](https://eval.16x.engineer/blog/the-pink-elephant-negative-instructions-llms-effectiveness-analysis)）

11. **附加理由（Why）帮助解决边界情况**——"TypeScript strict mode prevents type errors that reach production — never use any" 比单纯 "never use any" 更有效（来源：[dawid.ai Reddit 挖掘](https://dawid.ai/i-spent-40-hours-mining-reddit-for-the-techniques-that-actually-work/)）

12. **"IMPORTANT"/"YOU MUST" 强调有效,但滥用稀释效果**（来源：[官方 best-practices](https://code.claude.com/docs/en/best-practices)）

13. **重复规则 3 次不提升遵从率**——根因是 CLAUDE.md 是 advisory 级别,非 system 级别（来源：[GitHub Issue #15443](https://github.com/anthropics/claude-code/issues/15443)）

### 四、模块化架构

14. **@import 语法**：`@path/to/file` 引用外部文件,最深 5 级。官方原文："Imported files can recursively import other files, with a maximum depth of five hops."（来源：[官方 memory 文档](https://code.claude.com/docs/en/memory)）✅ 已验证

15. **.claude/rules/*.md**：无 `paths` frontmatter 的规则每次会话全量加载；有 `paths: ["src/api/**/*.ts"]` 的规则仅在 Claude 读取匹配路径文件时触发（来源：[官方 memory 文档](https://code.claude.com/docs/en/memory)）✅ 已验证

16. **AGENTS.md 互操作**：官方推荐 CLAUDE.md 用 `@AGENTS.md` 引用,而非保持逐行一致。官方原文："If your repository already uses AGENTS.md for other coding agents, create a CLAUDE.md that imports it so both tools read the same instructions without duplicating them."（来源：[官方 memory 文档](https://code.claude.com/docs/en/memory)）✅ 已验证

17. **四层模型**（社区共识）：
    - 宪法层（根 CLAUDE.md, ~60-80 行）→ 始终加载
    - 修正层（子目录 CLAUDE.md / .claude/rules/）→ 按需加载
    - 知识库（.pipeline/）→ 显式 @reference
    - 按需层（skills, subagents）→ 调用时加载

### 五、Hooks vs CLAUDE.md

18. **机械性规则应转为 hooks**：CLAUDE.md 是 advisory（Claude 尝试遵守），hooks 是 deterministic（确定性执行,不可跳过）。对"必须零例外执行"的规则,用 hooks 而非 CLAUDE.md（来源：[官方 best-practices](https://code.claude.com/docs/en/best-practices)、全部来源共识）

19. **候选 hook 化的规则**（机械性强,适合确定性执行）：
    - git commit after changes（PostToolUse hook）
    - git backup before editing（PreToolUse hook）
    - CLAUDE.md/AGENTS.md sync check（PostToolUse hook）
    - linter/formatter enforcement（Stop hook）

### 六、反模式（应避免）

20. **LLM 生成的指令内容**——降低性能 + 增加成本（ETH Zurich 研究,见 #6-7）
21. **目录结构/架构概述**——agent 自发现更优（见 #8）
22. **代码风格规则（linter 可执行的）**——"Never send an LLM to do a linter's job"（来源：[HumanLayer 博客](https://www.humanlayer.dev/blog/writing-a-good-claude-md)）
23. **叙事性背景段落**——代码任务中被 Claude 的相关性过滤器降权
24. **过时的结构描述**——"become liabilities when the codebase changes"（来源：[notchrisgroves.com](https://notchrisgroves.com/when-agents-md-backfires/)）
25. **频繁变动的信息**——嵌入 CLAUDE.md 后变成过时负担

### 七、诊断与调试

26. **Anthropic 官方诊断步骤**（来源：[官方 best-practices](https://code.claude.com/docs/en/best-practices)）：
    - 规则反复被违反 → 文件太长,规则被噪音淹没
    - Claude 问 CLAUDE.md 中已有答案的问题 → 措辞模糊
    - 同一问题纠正 >2 次 → `/clear` 重启
    - 运行 `/memory` 检查文件是否被加载

27. **Boris Cherny（Claude Code 创造者）**：把 CLAUDE.md 当测试套件——Claude 犯错时更新,行为已正确时裁剪（来源：[Twitter thread](https://twitter-thread.com/t/2007179832300581177)）

### 八、量化研究

28. **Arize AI meta-prompting 研究**：通过 LLM 优化 CLAUDE.md 本身,通用编码能力 +5.19%,仓库特定优化 +10.87%（来源：[Arize blog](https://arize.com/blog/claude-md-best-practices-learned-from-optimizing-claude-code-with-prompt-learning/)）

## 结论

**对 DQN10 的直接影响**：

1. **减体积是最高优先级**：当前 192 行在官方 200 行上限边缘,36 条规则 + 系统 ~50 条 = ~86 条,尚在预算内但无余量。提取参考性内容（环境表/命令/记忆地图/踩坑）到 `.claude/rules/` 可将根文件压到 ~80-100 行。

2. **NEVER → MUST 正面重构**：当前 10 条 NEVER（占 28%）超过推荐的 10%。可转换 5-6 条。

3. **#23 硬规则需重新评估**：官方推荐 `@AGENTS.md` import 方式而非逐行一致。维持现状可行但增加维护负担。

4. **机械性规则 hook 化**（#7 git commit、#8 git backup、#23 sync check）——从 advisory 升级为 deterministic,释放指令预算。

5. **删除可自发现的内容**：目录结构树（ETH 研究证实无效）、叙事性背景。

## 参考文献

### 官方来源
- [Anthropic — How Claude remembers your project](https://code.claude.com/docs/en/memory) — CLAUDE.md 规范、@import、.claude/rules/、AGENTS.md
- [Anthropic — Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices) — 写作建议、长度控制、诊断
- [anthropics/claude-code-action CLAUDE.md](https://github.com/anthropics/claude-code-action/blob/main/CLAUDE.md) — Anthropic 内部实例

### 实证研究
- [Gloaguen et al., ETH Zurich, arXiv:2602.11988](https://arxiv.org/abs/2602.11988) — AGENTS.md 有效性评估（2026-02）
- [Liu et al., "Lost in the Middle", arXiv:2307.03172](https://arxiv.org/abs/2307.03172) — 首尾偏差（2023）
- [Chroma — Context Rot](https://www.trychroma.com/research/context-rot) — 输入长度 vs 性能退化
- [Arize AI — CLAUDE.md Prompt Learning](https://arize.com/blog/claude-md-best-practices-learned-from-optimizing-claude-code-with-prompt-learning/) — Meta-prompting 量化研究

### 技术分析
- [HumanLayer — Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) — 注入机制、指令预算
- [16x Engineer — The Pink Elephant Problem](https://eval.16x.engineer/blog/the-pink-elephant-negative-instructions-llms-effectiveness-analysis) — NEVER vs MUST 效果分析
- [dawid.ai — 40 Hours Mining Reddit](https://dawid.ai/i-spent-40-hours-mining-reddit-for-the-techniques-that-actually-work/) — 社区技巧汇总

### 社区实践
- [flonat/claude-research](https://github.com/flonat/claude-research) — PhD 研究者 Claude Code 基础设施
- [abhishekray07/claude-md-templates](https://github.com/abhishekray07/claude-md-templates) — 模板库
- [Boris Cherny Twitter thread](https://twitter-thread.com/t/2007179832300581177) — CLAUDE.md 作为"活的制度记忆"
- [GitHub Issue #15443](https://github.com/anthropics/claude-code/issues/15443) — 规则遵从失败记录

### 综合指南
- [shareuhack.com — Claude Code CLAUDE.md Setup Guide 2026](https://www.shareuhack.com/en/posts/claude-code-claude-md-setup-guide-2026)
- [dev.to — CLAUDE.md Best Practices from Basic to Adaptive](https://dev.to/cleverhoods/claudemd-best-practices-from-basic-to-adaptive-9lm)
- [notchrisgroves.com — When AGENTS.md Backfires](https://notchrisgroves.com/when-agents-md-backfires/)
- [Augment Code — How to Build Your AGENTS.md 2026](https://www.augmentcode.com/guides/how-to-build-agents-md)
