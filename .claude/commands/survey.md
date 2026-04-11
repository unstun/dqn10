---
description: 文献调研：先确认搜索方向，再执行搜索，结果存入 .pipeline/literature/
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 DQN10 Literature Scout。执行文献调研前先和用户对齐方向。

## 第一步：读取现有文献

```
bigmemory/热区/状态简报.md              # 当前研究方向
.pipeline/literature/index.md           # 已有文献索引
.pipeline/terminology/terminology.md    # 术语规范
```

## 第二步：展示搜索计划，等待确认

用 `AskUserQuestion` 展示：

> 准备搜索以下方向的文献：
> 1. [方向 A]（关键词：...）
> 2. [方向 B]（关键词：...）
> 3. [方向 C]（关键词：...）
>
> 目标：约 20-30 篇，已有 X 篇
> 技能：inno-deep-research + paper-finder

选项：
- `确认，开始搜索`
- `调整搜索方向`
- `只搜某个方向`

如果用户选择调整，`AskUserQuestion` 询问具体方向修改，更新后再确认一次。

## 第三步：执行搜索（仅在确认后）

调用 `inno-deep-research` 和 `paper-finder` skills 执行搜索：

- 每个方向至少找 5 篇
- 逐条追加到 `.pipeline/literature/index.md`（格式：`| CitationKey | 标题 | 作者 | 年份 | 会议/期刊 | DOI | 关联度 | 备注 |`）
- PDF 存到 `1_survey/papers/<CitationKey>.pdf`
- 完成后写调研结论到 `.pipeline/survey/<主题关键词>.md`

## 第四步：展示结果摘要

结果回来后告诉用户：

- 新增了多少篇（总计多少篇）
- 主要覆盖了哪些方向
- 调研结论中的关键发现

用 `AskUserQuestion` 询问：
- `够了，回到 /plan 规划下一步`
- `还需要补充搜索某个方向`
- `看看调研结论后再决定`
