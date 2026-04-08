# Agent Handoff Log

每次会话结束前追加一个 `## Handoff:` 块。Stop hook 会检查本文件 mtime（MAX_AGE=300s）。

---

## Handoff: DQN10 bootstrapped from 机器狗RL + DQN9 merge — 2026-04-08

**状态**：脚手架初始化完成（Steps 1–5 of 7）

**已完成**：
- `.claude/{scripts,agents,commands,skills}` + `.pipeline/papers/` 目录骨架
- Hooks：`session-start.sh`（git log/status + handoff tail + top todo）、`stop-check.sh`（MAX_AGE=300s，verbatim from 机器狗RL）
- `settings.json` 接线两个 hook，timeout=10s
- `.pipeline/` 6 个初始文件（本文件 + project_truth / tasks / ledger / literature_bank / terminology）

**待办**：
- Step 4：复制 `.claude/agents/*.md`、`.claude/commands/*.md`（verbatim from 机器狗RL）
- Step 5：复制 `Oh-my--paper/skills/` 下 10 个 skill 目录 + 精简 `research-catalog.json`
- Step 6：写 `CLAUDE.md`（≡`AGENTS.md`）+ `check-agents-sync.sh` + `.gitignore` + `README.md`
- Step 7：自检 + `git init && commit`
- 遗留研究项：PreCompact hook 最佳实践调研（见 tasks.json）

**下一会话首动作**：继续 Step 4（复制 agents/commands 目录）。

---

## Handoff: DQN9 → DQN10 代码/论文/runs 迁移完成 — 2026-04-08

**目标**：让 DQN10 具备复现 DQN9 训练/推理/baseline 对比/论文写作的全部能力。

**已完成**：
- `rsync` 迁移(含排除 `__pycache__` / `*.pyc` / `.DS_Store` / LaTeX 中间产物):
  - `ugv_dqn/` (8.9M) + `train.py` + `infer.py`
  - `configs/` (1.0M) + `scripts/` (260K) + `paper/` (99M)
  - `runs20260408_dqn/` (6.9G) + `runs20260408_ddqn/` (7.0G) —— §4.5 cnn-dqn vs cnn-ddqn 底座消融(12 train + 24 infer × 2 底座)
- Git remote 指向 `https://github.com/unstun/dqn10.git`,通过 `pull --rebase --allow-unrelated-histories` 把本地 commit 接到 GitHub 占位 commit fcdc772 上,`push` 成功。
- `CLAUDE.md` 合并:DQN10 会话协议(你是谁/记忆地图/Conductor-Worker/Compact 须知) + DQN9 硬规则(21 条) + 实验数据结构(SR vs Quality 模式/CSV 三层) + 远程服务器表 + 常用命令 + 踩坑,**实际 153 行**(目标 ≤200)。每条硬规则 1 句话,共 35 条。
- `AGENTS.md` 同步完毕,`bash .claude/scripts/check-agents-sync.sh` PASS。
- 硬编码路径修正(§4.5 核心 6 个脚本):
  - `scripts/aggregate_20260408_raw.py` + `scripts/plot_loss_20260408_modules.py` : `ROOT = Path("/Users/.../DQN9")` → `Path(__file__).resolve().parent.parent`(跟随脚本位置)
  - `scripts/auto_pipeline_cnn_dqn.sh` / `launch_12par_cnn_dqn.sh` / `launch_24par_cnn_dqn_infer.sh` : `PROJ=/home/ubuntu/DQN9` → `/home/ubuntu/DQN10`
  - `scripts/collect_cnn_dqn_to_xlsx.py` : docstring + `--runs-root` help 文本 DQN9 → DQN10
- 新增 `configs/repro_20260408_dqn10_init.json`:完整登记迁移范围、路径修正清单、未改的旧脚本、验证命令——满足硬规则 #16。
- Mac 冒烟测试: `python -c "import ugv_dqn; from ugv_dqn.cli import train; from ugv_dqn.cli import infer"` 通过,`ugv_dqn.__file__` = `/Users/.../DQN10/ugv_dqn/__init__.py`。(`--self-check` 需 CUDA,Mac 是 CPU PyTorch,跳过,本机只做 import 级验证。)

**未迁移 / 保持 DQN9 路径**:
- `runs202643` / `runs202642`(旧论文定稿数据,不是当前 §4.5 焦点)
- `docs/experiment_framework.md`(Dr Sun: 评估框架不对先不迁移)
- `runs/`(老 AM×DQfD / kt=0.2 消融数据未迁移)——配套脚本 `scripts/deploy_server.py` / `quality_analysis.py` / `aggregate_abl_amdqfd.py` / `aggregate_ablation_kt02.py` 仍写 DQN9 路径,等真正需要复跑时再改。

**验证**:
- `check-agents-sync.sh` PASS
- `CLAUDE.md` 153 行(≤200 目标)
- `ugv_dqn` import 通过且路径正确
- Git push 到 `unstun/dqn10` 成功

**下一会话首动作**:DQN10 的 §4.5 cnn-dqn vs cnn-ddqn 工作继续。如要跑本地聚合,直接 `python scripts/aggregate_20260408_raw.py` 即可(路径已自适应)。如要远端跑全流水线,先按硬规则 #18 做 `rsync` 到 `/home/ubuntu/DQN10/`。

