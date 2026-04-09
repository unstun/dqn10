# .pipeline/ — 项目知识库(平文件数据库)

> 与 `bigmemory/`(会话记忆,按时间衰减)互补。
> `.pipeline/` 存放**长期有效的结构化项目知识**,不按天归档,不自动过期。

## 数据库清单

| 目录 | 用途 | 格式 |
|------|------|------|
| `terminology/` | 术语规范表 | 单文件 Markdown 表格 |
| `literature/` | 文献库(已读/待读论文索引) | 每篇一条,Markdown 表格 |
| `survey/` | 综述库(调研主题→结论→出处) | 每个主题一个 `.md` |
| `experiments/` | 实验台账(run→config→结果→结论) | 每轮实验一个 `.md` |
| `papers/` | 论文 PDF 本地副本 | symlink → `1_survey/papers/` |

## 维护时机

- **自动**:`/archive` 会话结束时,按分诊结果更新相关库
- **手动**:任何时候都可以直接编辑
