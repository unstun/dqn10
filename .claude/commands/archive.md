归档本次会话到 bigmemory + .pipeline/ 知识库。

## 主 AI 执行流程

### Step 0: 导出会话记录

立即执行:
```bash
python3 .claude/scripts/dump_conversation.py
```

### Step 1: 写摘要 + 派诊断 Agent

撰写本次对话的**完整摘要**(改了什么、为什么、关键决策、踩过的坑、读过的文献、跑过的实验)。

然后启动 1 个诊断 Agent(**sonnet**),prompt 包含:
- 摘要
- bigmemory 绝对路径
- 当前日期时间
- 下方"诊断 Agent 指令"全文

### Step 2: 接收分诊结论 → 派 5 个 Worker

诊断 Agent 返回后,根据其分诊结论,在**同一条消息**中启动 5 个 Worker(**sonnet**)。

每个 Worker 的 prompt 须包含:
1. 当前日期时间 + bigmemory 绝对路径
2. 对话摘要
3. 诊断 Agent 返回的分诊结论(哪些 Q 通过 + 当前热区状态)
4. 指令"先读 `bigmemory/格式规范.md`"

### Step 3: 汇总 + Git 备份

5 个 Worker 全部返回后:
1. `git status --short`
2. **只 add 本次归档写入的文件**(禁止 `git add .`)
3. `git commit -m "chore(bigmemory): archive <一句话摘要>"`
4. 有远程仓库则 `git push`
5. 输出归档报告

```
=== 归档完成 ===
改动记录：✓ / ✗(原因) / —
踩坑记录：✓ / ✗(原因) / —
调研记录：✓ / ✗(原因) / —
心路历程：✓ / ✗(原因) / —
里程碑：  ✓ / ✗(原因) / —
会话记录：✓ dump_conversation.py 已导出
热区瘦身：状态简报 [N字] | 未关闭决策 [N字] | 近期改动 [N字]
偏好/工作流：✓ 更新 / 无变更
.pipeline/：literature ✓/— | experiments ✓/— | survey ✓/— | terminology ✓/—
冷区降级：处理 N 个文件 / 无需降级
Git 备份：✓ 提交 [hash] + 推送 / ✓ [hash] 仅本地 / — 无变更
未纳入文件：[无 / 列表]
```

---

## 诊断 Agent 指令

读取以下文件:
- `bigmemory/热区/状态简报.md`
- `bigmemory/热区/未关闭决策.md`
- `bigmemory/热区/近期改动.md`
- `bigmemory/冷区/偏好.md`
- `bigmemory/冷区/工作流.md`
- `bigmemory/格式规范.md`

根据主 AI 提供的对话摘要,回答分诊问题:

**bigmemory 分诊**:
- Q1: 是否产生了代码/配置改动? → 冷区/改动记录
- Q2: 是否遇到非显而易见的问题(调查超 5 分钟)? → 冷区/踩坑记录
- Q3: 是否获取了外部信息? → 冷区/调研记录
- Q4: 是否涉及重要决策或方向变化? → 冷区/心路历程
- Q5: 是否完成重大里程碑? → 冷区/里程碑

**.pipeline/ 分诊**:
- Q7: 是否涉及新文献? → `.pipeline/literature/index.md`
- Q8: 是否产生实验数据? → `.pipeline/experiments/YYYYMMDD_<topic>.md`
- Q9: 是否完成一次主题调研? → `.pipeline/survey/<topic>.md`
- Q10: 是否定义/修改了术语? → `.pipeline/terminology/terminology.md`

Q6(会话记录)已由 Step 0 自动处理。

**返回格式**(严格遵守,主 AI 依赖此格式派 Worker):

```
## 分诊结论
Q1: YES/NO — [一句话理由]
Q2: YES/NO — [一句话理由]
Q3: YES/NO — [一句话理由]
Q4: YES/NO — [一句话理由]
Q5: YES/NO — [一句话理由]
Q7: YES/NO — [一句话理由]
Q8: YES/NO — [一句话理由]
Q9: YES/NO — [一句话理由]
Q10: YES/NO — [一句话理由]

## 当前热区状态
[状态简报.md 核心内容摘要]
[未关闭决策.md 核心内容摘要]
[近期改动.md 核心内容摘要]

## 偏好/工作流变更检测
[对比摘要与现有偏好.md/工作流.md,指出需新增/修改的条目,或"无变更"]

## 冷区查重
[Grep 冷区搜索本次关键词,列出已存在的相关记录,避免 Worker 重复写入]
```

不要写入任何文件,只返回分诊结论。

---

## Worker 职责

**Worker 1: 冷区事实层**(改动记录 + 踩坑记录)
- 写入分诊通过的 Q1/Q2 条目
- 追加模式,写前 Grep 查重

**Worker 2: 冷区认知层**(调研记录)
- 写入分诊通过的 Q3 条目
- 调研记录必须包含 URL 或文献标识
- 若 Q3 = NO,报告"无需写入"即可

**Worker 3: 冷区决策层**(心路历程 + 里程碑 + 偏好/工作流)
- 写入分诊通过的 Q4/Q5 条目
- 根据诊断 Agent 的"偏好/工作流变更检测"结果更新对应文件

**Worker 4: 热区瘦身**
- 根据诊断 Agent 提供的"当前热区状态",全量重写 3 个热区文件
- 严格遵守容量预算(状态简报 ≤1500字, 未关闭决策 ≤1200字, 近期改动 ≤1000字)
- 写后 `wc -m` 校验

**Worker 5: .pipeline/ 知识库 + 冷区降级**
- 写入分诊通过的 Q7-Q10 条目,按各库 README.md 格式
- 冷区降级: 31-90天加摘要头,91-365天合并月度摘要,365+天年度摘要
- 更新 `.degradation-state.json`

## 不归档的内容

- 纯闲聊、无实质进展的对话
- 已在代码/git 中有充分记录的细节
- 临时调试过程(只记结论)
- 简单格式调整、拼写修正
- 重复信息(冷区已有几乎相同的记录)

## 模型选择

- Claude Code: 诊断 Agent + 5 Workers 均用 **sonnet**
- Droid: 诊断 Agent + 5 Workers 均用 **gpt-5.4-mini**
