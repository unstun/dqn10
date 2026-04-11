---
paths: ["bigmemory/**", ".pipeline/**"]
---
# 记忆系统详细结构

## bigmemory/(按需拉取,透明读写)

- `热区/状态简报.md` — 当前项目状态(≤1500字)
- `热区/未关闭决策.md` — 未关闭的研究/技术决策(≤1200字)
- `热区/近期改动.md` — 最近 7 天改动摘要(≤1000字)
- `冷区/改动记录/` — 按天归档:YYYY-MM-DD.md(只追加)
- `冷区/踩坑记录/` — 按天归档(只追加)
- `冷区/调研记录/` — 按天归档(只追加)
- `冷区/心路历程/` — 按天归档(只追加)
- `冷区/里程碑/` — 按天归档(只追加)
- `冷区/偏好.md` — 用户偏好(单文件)
- `冷区/工作流.md` — 标准工作流(单文件)
- `格式规范.md` — 热区容量预算 + 冷区文件格式模板

**读写规则**:冷区按天文件只追加不覆写,热区全量重写且须遵守容量预算(见 `bigmemory/格式规范.md`)。

## .pipeline/(项目知识库,平文件数据库)

- `terminology/` — 术语规范表(中英文术语、禁用词)
- `literature/` — 文献库(已读/待读论文索引,index.md 为主表)
- `survey/` — 综述库(每个调研主题一个 `.md`)
- `experiments/` — 实验台账(每轮实验一个 `YYYYMMDD_<topic>.md`)
- `papers/` → symlink 到 `1_survey/papers/`(命名 `<CitationKey>.pdf`,付费墙材料加 `_supp` 后缀)

与 bigmemory(会话记忆,按时间衰减)互补;`.pipeline/` 存放长期有效的结构化项目知识,不自动过期。

## 记忆检索模型

统一使用 `memory-retrieval` skill(`.claude/skills/memory-retrieval/SKILL.md`）：
- 主路径：auggie（Augment Context Engine）语义检索 bigmemory/ + .pipeline/
- 回退：auggie 不可用时降级为 Grep + Read 手动检索
- 旧 memory-worker droid（`.factory/droids/memory-worker.md`）已 deprecated,仅留存参考

## 记忆出入口

**入口(自动)**:Dr Sun 第一句话后,主 AI 自动触发 `memory-retrieval` skill,通过 auggie 从 bigmemory/ 和 .pipeline/ 语义检索相关上下文。

**出口(手动)**:Dr Sun 调用 `/archive`,主 AI 执行分诊 + 冷区归档 + 热区刷新 + `.pipeline/` 知识库更新。

- 多 Agent 并行写入
- 所有写入在对话中透明进行(用户可见)
