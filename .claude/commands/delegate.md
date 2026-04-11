---
description: 为代码/实验任务生成 Codex prompt，用户复制到新终端执行
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 DQN10 Conductor。此命令专用于需要 Codex 执行的**代码和实验任务**。

## 第一步：读取上下文

```
bigmemory/热区/状态简报.md
bigmemory/热区/未关闭决策.md
.pipeline/experiments/                  # 已有实验台账
.pipeline/terminology/terminology.md
```

## 第二步：展示计划，等待确认

用 `AskUserQuestion` 向用户展示将要委派的任务摘要：

- **任务内容**：用 1-2 句话描述将交给 Codex 做什么
- **注入的上下文**：列出将附带哪些背景信息
- **输出位置**：Codex 完成后产出写入哪里

选项：
- `确认，生成 prompt`
- `我来调整任务描述`
- `取消`

## 第三步：生成 Codex prompt（仅在确认后）

构建完整 prompt，格式如下：

```
[项目背景]
研究主题：（从状态简报提取）
代码包名：ugv_dqn（继承自 DQN9）
实验目录：2_experiment/

[已有实验记录 - 避免重复]
（.pipeline/experiments/ 下最近 3 个台账的标题和结论）

[你的任务]
（确认后的任务描述）

[输出要求]
- 代码改动写入 2_experiment/ 目录
- 实验结束后在 .pipeline/experiments/ 新建台账 YYYYMMDD_<topic>.md
- 遵守 .pipeline/terminology/terminology.md 中的术语规范
```

## 第四步：展示给用户复制执行

用代码块展示完整命令，告知用户在**新终端**里执行：

```
在新终端里运行：
codex "[完整 prompt]"

或后台运行：
codex --background "[完整 prompt]"
```

用 `AskUserQuestion` 询问：
- `我已经在新终端里跑起来了`
- `取消`

## 第五步：等待完成，读取结果

用户确认跑起来后，检查产出：

```bash
ls .pipeline/experiments/ | tail -5
git log --oneline -5
```

读取结果后向用户简要说明：做了什么、产出了哪些文件、有没有问题。

用 `AskUserQuestion` 询问：
- `接受结果，继续下一步`
- `需要修改某处`
- `这个结果有问题，放弃`
