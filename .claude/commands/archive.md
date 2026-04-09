归档本次会话到 bigmemory + .pipeline/ 知识库。按以下步骤执行:

## 1. 分诊(逐条判断)

**bigmemory 分诊**:
- Q1: 是否产生了代码/配置改动? → 写 `bigmemory/冷区/改动记录/YYYY-MM-DD.md`
- Q2: 是否遇到非显而易见的问题(调查超过 5 分钟)? → 写 `bigmemory/冷区/踩坑记录/YYYY-MM-DD.md`
- Q3: 是否获取了外部信息(联网搜索/论文/文档)? → 写 `bigmemory/冷区/调研记录/YYYY-MM-DD.md`
- Q4: 是否涉及重要决策或方向变化? → 写 `bigmemory/冷区/心路历程/YYYY-MM-DD.md`
- Q5: 是否完成重大里程碑? → 写 `bigmemory/冷区/里程碑/YYYY-MM-DD.md`
- Q6: 本次会话是否有值得保留的对话内容(推理链、讨论、决策过程)? → 写 `bigmemory/冷区/会话记录/YYYY-MM-DD.md`

**.pipeline/ 分诊**:
- Q7: 是否涉及新文献(读了论文/搜了参考文献)? → 更新 `.pipeline/literature/index.md`
- Q8: 是否产生实验数据(训练/推理/消融)? → 写 `.pipeline/experiments/YYYYMMDD_<topic>.md`
- Q9: 是否完成一次主题调研? → 写 `.pipeline/survey/<topic>.md`
- Q10: 是否定义/修改了术语? → 更新 `.pipeline/terminology/terminology.md`

全部为否 → 输出"无需归档",终止。

## 2. 多 Agent 并行写入

将分诊通过的类别分为**独立任务**,派多个 subagent 并行执行:

- Agent 模型:Claude Code 用 `sonnet`,Droid 用 `gpt-5.4-mini`
- 每个 agent 负责一个写入目标(bigmemory 冷区某类 + .pipeline/ 某库)
- 主会话提供本次会话摘要作为 agent prompt 的上下文

**分组建议**(可合并相关性强的):
- Agent A: bigmemory 冷区写入(改动记录 + 踩坑 + 心路历程 + 里程碑)
- Agent B: bigmemory 冷区写入(调研记录 + 会话记录)
- Agent C: .pipeline/ 知识库更新(literature + experiments + survey + terminology)

冷区按天文件按 `bigmemory/格式规范.md` 模板写入,已存在则追加。
.pipeline/ 按各库 `README.md` 格式写入。

## 3. 刷新热区(主会话执行,不派 agent)

- `bigmemory/热区/状态简报.md`: 更新当前任务 + 关键上下文 + 警告(≤1500字)
- `bigmemory/热区/未关闭决策.md`: 新增/关闭决策(≤1200字)
- `bigmemory/热区/近期改动.md`: 更新 7 天滚动窗口(≤1000字)

## 4. 校验

用 `wc -m` 检查热区文件是否在容量预算内,超限则压缩。
