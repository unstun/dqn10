# DQN10

DQN9 的后继项目。工作流脚手架迁移自 `机器狗RL/.claude/` + `Oh-my--paper/skills/`，算法/论文硬规则继承自 DQN9。

## 目录结构

```
DQN10/
├── CLAUDE.md              # 项目规则（≡ AGENTS.md）
├── AGENTS.md              # 同上，逐行一致
├── README.md
├── .claude/
│   ├── settings.json      # SessionStart + Stop hooks
│   ├── scripts/           # session-start.sh, check-agents-sync.sh, *.mjs
│   ├── agents/            # 5 个 subagent（conductor/experiment-driver/literature-scout/paper-writer/reviewer）
│   ├── commands/          # slash commands（plan/survey/experiment/write/review/delegate/archive/sync/setup/ideate）
│   └── skills/            # skills + research-catalog.json
├── .pipeline/             # 项目知识库（平文件数据库）
│   ├── README.md
│   ├── literature/        # 文献库
│   │   ├── README.md
│   │   └── index.md       # 文献索引表
│   ├── terminology/       # 术语规范
│   │   └── terminology.md
│   ├── experiments/       # 实验台账（每轮一个 YYYYMMDD_topic.md）
│   │   └── README.md
│   └── survey/            # 综述库（每个主题一个 .md）
│       └── README.md
├── bigmemory/             # 会话记忆（按时间衰减）
│   ├── 热区/              # 状态简报、未关闭决策、近期改动
│   └── 冷区/              # 会话记录、改动记录、踩坑记录、里程碑等
├── 1_survey/papers/       # 论文 PDF 本地副本
├── 2_experiment/          # 实验代码
│   ├── configs/
│   ├── scripts/
│   ├── ugv_dqn/           # 核心包
│   └── runs*/             # 实验输出
├── 3_paper/               # 论文
│   ├── main.tex           # 论文主文件（单文件）
│   ├── references.bib
│   ├── figures/
│   ├── results/
│   └── writing_rules.md
└── llm-local-knowledge-cache/  # LLM 本地知识缓存调研
```

## 首次启动

1. 会话开始时 memory-retrieval skill 自动从 bigmemory 检索相关上下文。
2. 结束前通过 `/archive` 归档到 `bigmemory/` + `.pipeline/`。
3. 修改 `CLAUDE.md` 后必须 `cp CLAUDE.md AGENTS.md` 并跑 `bash .claude/scripts/check-agents-sync.sh`。
