# DQN10

DQN9 的后继项目。工作流脚手架迁移自 `机器狗RL/.claude/` + `Oh-my--paper/skills/`,算法/论文硬规则继承自 DQN9。

## 目录结构

```
DQN10/
├── CLAUDE.md          # 项目规则(≡ AGENTS.md)
├── AGENTS.md          # 同上,逐行一致
├── .claude/
│   ├── settings.json  # SessionStart + Stop hooks
│   ├── scripts/       # session-start.sh, stop-check.sh, check-agents-sync.sh, *.mjs
│   ├── agents/        # 5 个 subagent
│   ├── commands/      # 9 个 slash command
│   └── skills/        # 10 个 skill + research-catalog.json(精简版)
└── .pipeline/
    ├── project_truth.md
    ├── agent_handoff.md
    ├── tasks.json
    ├── experiment_ledger.md
    ├── literature_bank.md
    ├── terminology.md
    └── papers/
```

## 首次启动

1. 会话开始时 SessionStart hook 自动输出 git 快照 + 上次交接 + 下一个 todo。
2. 结束前追加 `.pipeline/agent_handoff.md`,Stop hook 会校验 mtime(MAX_AGE=300s)。
3. 修改 `CLAUDE.md` 后必须 `cp CLAUDE.md AGENTS.md` 并跑 `bash .claude/scripts/check-agents-sync.sh`。

## 遗留 TODO

- PreCompact hook 强制落盘方案调研(见 `.pipeline/tasks.json`)。
