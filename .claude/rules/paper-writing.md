---
paths: ["3_paper/**", "**/*.tex", "**/*.bib"]
---
# 论文写作规则

## 语言与写作流

- MUST:论文正文先中文写作,定稿后统一英文润色,README 等项目文档也用中文。
- MUST:论文润色工作流——多 Agent 并行搜同领域真实句子 → 提炼句式特征 → 按句式改写并标注对标原句 → 自检是否丢失信息。

## 引用核查四步

1. `search_web` / Semantic Scholar 定位论文
2. DOI 2 源交叉确认
3. `curl -LH "Accept: application/x-bibtex" https://doi.org/<DOI>` 获取 BibTeX
4. 确认 claim 在原文中存在

失败标 `[CITATION NEEDED]`,严禁凭记忆生成 BibTeX。

## 禁止事项

- NEVER:使用括号补充说明(缩写定义除外,如"深度强化学习(DRL)"),改用"即""由…构成""如图…所示"。
- NEVER:公式中使用 `grid_size` 等代码风格变量名,须用 $\Delta c$、$\delta$、$\epsilon$ 等标准记法,独立公式末尾不加标点。
- NEVER:方法论写 enumerate 列表式段落,须散文叙事。
- NEVER:捏造术语、过度包装简单概念、使用推销性语言,术语须溯源文献。
