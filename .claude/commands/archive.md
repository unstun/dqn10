归档本次会话到 bigmemory + .pipeline/ 知识库。

## 主 AI 职责(仅此三步)

### Step 0: 导出会话记录

立即执行:
```bash
python3 .claude/scripts/dump_conversation.py
```
此脚本自动找到当前会话的 JSONL,导出主会话 + 所有 subagent 到 `bigmemory/冷区/会话记录/YYYY-MM-DD_HHMM.md`。

### Step 1: 启动协调 Agent

撰写本次对话的**完整摘要**(改了什么、为什么、关键决策、踩过的坑、读过的文献、跑过的实验),然后启动 1 个协调 Agent(sonnet),将摘要 + 以下指令传入。

### Step 2: 转发报告

协调 Agent 返回后,将归档报告原样展示给 Dr Sun。

---

## 协调 Agent 指令(以下内容作为 prompt 传入)

### Phase 1: 读取状态 + 分诊

读取以下文件了解记忆系统当前状态:
- `bigmemory/热区/状态简报.md`
- `bigmemory/热区/未关闭决策.md`
- `bigmemory/热区/近期改动.md`
- `bigmemory/冷区/偏好.md`
- `bigmemory/冷区/工作流.md`
- `bigmemory/格式规范.md`

然后根据主 AI 提供的对话摘要,回答分诊问题:

**bigmemory 分诊**:
- Q1: 是否产生了代码/配置改动? → 冷区/改动记录
- Q2: 是否遇到非显而易见的问题(调查超 5 分钟)? → 冷区/踩坑记录
- Q3: 是否获取了外部信息? → 冷区/调研记录
- Q4: 是否涉及重要决策或方向变化? → 冷区/心路历程
- Q5: 是否完成重大里程碑? → 冷区/里程碑
- Q6: 是否有值得保留的对话内容? → 冷区/会话记录

**.pipeline/ 分诊**:
- Q7: 是否涉及新文献? → `.pipeline/literature/index.md`
- Q8: 是否产生实验数据? → `.pipeline/experiments/YYYYMMDD_<topic>.md`
- Q9: 是否完成一次主题调研? → `.pipeline/survey/<topic>.md`
- Q10: 是否定义/修改了术语? → `.pipeline/terminology/terminology.md`

全部为否 → 输出"无需归档",跳到 Phase 4。

### Phase 2: 派 5 个 Worker Agent 并行写入

在同一条消息中启动 5 个 Agent(sonnet),每个 Agent 的 prompt 须包含: 当前日期时间、bigmemory 绝对路径、对话摘要、分诊结果、指令"先读 `bigmemory/格式规范.md`"。

**Worker 1: 冷区事实层**(改动记录 + 踩坑记录)
- 写入分诊通过的 Q1/Q2 条目
- 追加模式,写前 Grep 查重

**Worker 2: 冷区认知层**(调研记录)
- 写入分诊通过的 Q3 条目
- 调研记录必须包含 URL 或文献标识
- Q6(会话记录)已由 Step 0 的 dump_conversation.py 自动处理,无需再写

**Worker 3: 冷区决策层**(心路历程 + 里程碑 + 偏好/工作流)
- 写入分诊通过的 Q4/Q5 条目
- 检查是否需要更新偏好.md 或工作流.md

**Worker 4: 热区瘦身**
- 冷区关联检索(Grep 搜关键词,发现重复踩坑/反复模式)
- 热区 3 个文件全量重写,严格遵守容量预算
- 写后 `wc -m` 校验

**Worker 5: .pipeline/ 知识库 + 冷区降级**
- 写入分诊通过的 Q7-Q10 条目,按各库 README.md 格式
- 冷区降级: 31-90天加摘要头,91-365天合并月度摘要,365+天年度摘要
- 更新 `.degradation-state.json`

### Phase 3: Git 备份

5 个 Worker 全部返回后:

1. `git status --short` 检查变更
2. **只 add 本次归档写入的文件**(禁止 `git add .`)
3. `git commit -m "chore(bigmemory): archive <一句话摘要>"`
4. 有远程仓库则 `git push`
5. 如有未暂存文件(非本次改动),记录到报告

### Phase 4: 输出归档报告

```
=== 归档完成 ===
改动记录：✓ / ✗(原因) / —
踩坑记录：✓ / ✗(原因) / —
调研记录：✓ / ✗(原因) / —
心路历程：✓ / ✗(原因) / —
里程碑：  ✓ / ✗(原因) / —
会话记录：✓ / ✗(原因) / —
热区瘦身：状态简报 [N字] | 未关闭决策 [N字] | 近期改动 [N字]
偏好/工作流：✓ 更新 / 无变更
.pipeline/：literature ✓/— | experiments ✓/— | survey ✓/— | terminology ✓/—
冷区降级：处理 N 个文件 / 无需降级
Git 备份：✓ 提交 [hash] + 推送 / ✓ [hash] 仅本地 / — 无变更
未纳入文件：[无 / 列表]
```

## 不归档的内容

- 纯闲聊、无实质进展的对话
- 已在代码/git 中有充分记录的细节
- 临时调试过程(只记结论)
- 简单格式调整、拼写修正
- 重复信息(冷区已有几乎相同的记录)

## 模型选择

- Claude Code: 协调 Agent + 5 Workers 均用 **sonnet**
- Droid: 协调 Agent + 5 Workers 均用 **gpt-5.4-mini**
