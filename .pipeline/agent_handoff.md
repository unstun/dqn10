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

---

## Handoff: PreCompact hook 调研任务 plan 已出,等待 Dr Sun 确认开始 — 2026-04-08

**本次会话做了什么**:

- 会话启动协议三件套读取完成:`agent_handoff.md`(tail) / `project_truth.md`(仍是占位) / `tasks.json`(唯一 todo = `research-precompact-hook`,medium)
- 按硬规则 #5 向 Dr Sun 报了 6 步调研计划 + 文件清单 + 风险 + 验证,等"开始"指令再执行

**计划摘要**(未执行):

1. `claude-code-guide` agent 查官方 hooks 文档里 `PreCompact` 事件 schema/触发时机/阻断语义
2. WebSearch 社区实践(每批 ≤2 同类调用,避免 WebFetch 403 级联)
3. 汇总 2–4 个方案对比优劣(shell 拦截 / 写 state 文件 / 与 Stop hook 分工)
4. 产出 `.pipeline/research/precompact_hook_best_practices.md`(新建)
5. `tasks.json` 标 `research-precompact-hook` done,按结论决定是否新增 `impl-precompact-hook`
6. 追加 handoff

**未执行的原因**:硬规则 #5 要求报计划后等"开始"。Dr Sun 未回复"开始",故不动手。本次被 Stop hook 提醒 handoff 超龄,于是先补这条占位 handoff,不变更计划本体。

**未改动任何文件**(除本 handoff 一条新增条目)。

**下一会话首动作**:若 Dr Sun 回复"开始",直接执行上述计划第 1 步;若 Dr Sun 改任务,重新读 `tasks.json`。

---

## Handoff: PreCompact hook 调研完成 — 2026-04-08

**任务**:`tasks.json#research-precompact-hook` → status=done。

**核心结论**(完整笔记 `.pipeline/research/precompact_hook_best_practices.md`,5 段 + 6 个参考链接):

1. **PreCompact hook 真实存在**,matcher 支持 `manual` / `auto` / `*`,输入含 `trigger` + `custom_instructions`(官方 doc <https://code.claude.com/docs/en/hooks>)
2. **不能 block compaction**——官方 exit code 表明确写 `PreCompact: Can block? No, exit 2 only shows stderr to user`。它是 side-effect 事件,不是 enforcement 事件。
3. **已知严重缺陷 anthropics/claude-code#13572**:多用户复现 PreCompact 在 manual `/compact` 完全不触发(2026-01 v2.1.7 macOS 也复现),issue 已被 bot 自动 inactive 关闭,**未见修复说明**。
4. **推荐方案 D 双轨**:
   - 轨 A `pre-compact.sh`:防 auto-compact,触发时往 handoff 写占位条目(session_id + cwd + trigger 原因)
   - 轨 B `/compact-safe` slash command:防 manual /compact,利用 EmanuelFaria workaround——`/compact <instructions>` 的 instructions 会插入 compaction prompt,强制 LLM 按 5 段式输出
   - 不上 who96 supervisor(过度复杂),不缩短 Stop hook MAX_AGE(逼自己塞水分)

**注意**:agent `claude-code-guide` 第一次返回的"PreCompact 是 read-only,不能 block"是**正确的**;但它编了一段 "documentation explicitly states ... read-only event for logging" 的引文是**伪造的**——硬规则 #12 兑现:对 AI 输出做了独立验证(WebFetch 官方 doc + WebSearch + gh issue view),才确认结论正确而非引文真实。

**已写入**:

- 新建 `.pipeline/research/precompact_hook_best_practices.md`(193 行)
- 改 `.pipeline/tasks.json`:`research-precompact-hook` → done,新增 `impl-precompact-hook` (medium, todo)
- 追加本条 handoff

**下一会话首动作**:

- 高优先级:无。可空闲 / 切其他任务。
- 中优先级:执行 `impl-precompact-hook`。落地前先 `claude --version` 确认当前版本,跑一次 manual `/compact` 实测 PreCompact 是否仍受 #13572 影响,再决定 4 个文件改动是否一次到位。
- 工程纪律:本次有 1 个未提交文件 + 1 个改动文件,Dr Sun 确认调研结果后再 commit。

---

## Handoff: CLAUDE.md 拟加 1 行"子 agent 引文可能是编的"踩坑 — 2026-04-08

**触发**:PreCompact 调研结束后,Dr Sun 让我把"子 agent 输出的官方引文可能是编造的"一句话固化进 CLAUDE.md(踩坑段)。

**已做**:

- 按硬规则 #5 报了 5 步计划 + 文件清单(CLAUDE.md + AGENTS.md 各 +1 行)+ 风险 + 验证 + 2 个候选措辞(A 精确归因 `claude-code-guide` / B 通用)
- 推荐 A,理由是日后回看能锚定 2026-04-08 PreCompact 调研那次具体踩坑来源

**未做 / 等待**:

- 等 Dr Sun 选 "开始 A" / "开始 B" / "换措辞 ..."
- 任何文件未改

**Stop hook 触发原因**:本会话从 compact 后到现在没动文件,handoff 自然超龄 300s。先补占位 handoff 让 Stop hook 放行,不变更计划本体。

**下一会话首动作**:

- 若 Dr Sun 已回"开始 A/B":Edit CLAUDE.md + AGENTS.md → `bash .claude/scripts/check-agents-sync.sh` → 追加 handoff 记录已落地;不单独 commit(和 PreCompact 调研产物一并)
- 若 Dr Sun 改任务:重新读 tasks.json
- 注意:`impl-precompact-hook` 仍 todo,按硬规则 #26 一次会话只做一件事,不能在同一会话顺手做

---

## Handoff: 候选措辞迭代到 A++,仍等拍板 — 2026-04-08

Dr Sun 提"联网真实信息能避免一部分 AI 幻觉"——对,但只降率不消灭(尤其 quote-fabrication 失败模式:LLM 可以同时正确 retrieve 概念事实 + 反向"补"出与源不逐字一致的引号)。据此把推荐版本从 A → A++:焦点从"全 verify"前移到"force grounding + 引号 spot-check"。

**当前 4 个候选**:

- A(原版):纯 verify-after
- A+(中间版):verify + prompt-time 显式禁伪造
- **A++(当前推荐)**:子 agent 调用必须强制 WebFetch/Grep 真实源 + 附 URL 原文片段;主会话只 spot-check 引号字段;结论性陈述若无引号可信度高
- B:通用版,不点名 agent

**仍未改动任何文件**(本会话纯讨论)。Stop hook 又超龄,先补占位 handoff。

**等**:`开始 A++` / `开始 A` / `开始 B` / `自己改措辞`。

---

## Handoff: 落地 A++ 时发现 CLAUDE.md ≠ AGENTS.md(#23 已破)— 2026-04-08

Dr Sun 已批 `开始 A++`。落地第 1 步读两个文件时发现 **CLAUDE.md (138 行) 与 AGENTS.md (153 行) 已经不一致**,`check-agents-sync.sh` exit=2(strict diff)。前一条 handoff 声称的 PASS 是历史快照,后续某次 commit 只动了 AGENTS.md 没同步 CLAUDE.md。

**7 处差异,关键 3 处(都是 CLAUDE.md 缺、AGENTS.md 有)**:

- `## 术语规范` 整段(Dijkstra 目标距离图 / MD vs DM 术语表)
- 实验数据结构里的 `算法名称映射`(MD-DQN / Improved HA* / SB-RRT*)
- 实验数据结构里的 `CSV 三层` + `核心对比 vs 消融 config 行数规约`

其余 4 处是表格格式(空格填充 vs 紧凑)、1 个空行差、"50 runs" vs "50+ runs"。

**含义**:主会话(claudeMd 注入的是 CLAUDE.md)在术语和算法映射上落后一个版本——本身就是个比 A++ 重要得多的修复。

**已停止 A++ 落地,改报 3 个候选给 Dr Sun**:

- (i) 先 sync(CLAUDE.md ← AGENTS.md)再加 A++,一次 commit 修两个问题(我推荐)
- (ii) 只加 A++ 不动同步,继续破 #23
- (iii) 先 sync(本会话),A++ 推到下个会话(严格守 #26)

**前置建议**:走 (i) 前先 `git log -p -- AGENTS.md CLAUDE.md` 30 秒考古(只读)锁定 sync 方向,确认不是有人故意精简 CLAUDE.md。

**仍未改动任何代码/文档文件**(只追加 handoff)。Stop hook 又超龄,先补占位。

**等**:`先做 git 考古` / `开始 (i)` / `开始 (ii)` / `开始 (iii)` / `换反向 sync`。

---

## Handoff: 综合快照(Dr Sun 喊"先总结上下文不够了")— 2026-04-08

> 本条是当前会话的**最终交接**,前面 4 条 handoff 都是过程记录,可跳读。下一会话只要读本条就够。

### 1. 当前任务一句话

在 `CLAUDE.md` 的 `## 踩坑` 段加 1 行 "子 agent 引文可能是编的"——但落地时发现 **`CLAUDE.md ≠ AGENTS.md`(硬规则 #23 已破)**,任务被卡在等 Dr Sun 选 sync 方向。

### 2. 待添加的踩坑措辞(A++,Dr Sun 已批,直接抄)

```text
- 子 agent(含 claude-code-guide)调用 prompt 必须强制其 WebFetch/Grep 真实源再答并附 URL + 原文片段。即便如此,LLM 仍会伪造与源不逐字对齐的"原文引号"(quote-fabrication 已知失败模式),所以主会话必须把引号字段与源 spot-check。结论性陈述若无引号,可信度高(硬规则 #12 的具体场景)。
```

来源:PreCompact 调研中 `claude-code-guide` agent 返回的"PreCompact is a read-only event for logging and audit purposes"是它编的——结论(PreCompact 不能 block)对,引号假。Dr Sun 提"联网真实信息能避免一部分幻觉"的直觉,A++ 把这个直觉固化:grounding 是主防线,只对引号 spot-check,不是 verify 一切。**不要重新讨论 A → A+ → A++ 的迭代历史,Dr Sun 已批 A++,直接用。**

### 3. 卡点:`check-agents-sync.sh` exit=2

**`CLAUDE.md`(138 行) ≠ `AGENTS.md`(153 行)**,7 处 diff。**关键 3 处全是 CLAUDE.md 缺、AGENTS.md 有**:

1. 整段 `## 术语规范`(Dijkstra 目标距离图 / MD vs DM 术语表),~11 行
2. 实验数据结构里的 **算法名称映射**:`CNN-DQN+Duel → MD-DQN`、`Hybrid A* → Improved HA*`(Dang 2022)、`RRT* → SB-RRT*`(Yoon 2018),LO-HA* 已弃用
3. 实验数据结构里的 **CSV 三层**(table2_kpis.csv / table2_kpis_mean.csv / table2_kpis_mean_filtered.csv)+ **核心对比 vs 消融 config 行数规约**(150 行 vs 50 行)

**次要 4 处**:CLAUDE.md 第 25 行多 1 个空行;环境表 + 远程服务器表格式(CLAUDE.md 空格填充对齐 vs AGENTS.md 紧凑 `|---|---|---|`);`50 runs` vs `50+ runs`;SR/Quality 列表前空行差。

**含义**:主会话被 Claude Code 注入的是项目根 `CLAUDE.md`,术语和算法映射**落后一个版本**,论文写作时会丢这 3 段。前一条 handoff 声称的 sync PASS 是历史快照,后续某次 commit 只动了 AGENTS.md。**具体哪个 commit 未考古。**

### 4. 等 Dr Sun 拍的 4 个候选

| 编号 | 行动 | 推荐度 |
|---|---|---|
| `先 git 考古` | `git log -p -- AGENTS.md CLAUDE.md`(只读)锁定 sync 方向,确认不是有人故意精简 CLAUDE.md | **强烈推荐先做这一步** |
| `开始 (i)` | sync(CLAUDE.md ← AGENTS.md 整体覆盖)+ 两边加 A++ + check-agents-sync PASS + 一次 commit | **主推荐** |
| `开始 (ii)` | 只加 A++ 不 sync,维持破 #23 | 不推荐 |
| `开始 (iii)` | 本会话 sync,A++ 推到下个会话(守 #26) | 备选 |

**推荐路径**:`先 git 考古` → 若方向是 CLAUDE.md ← AGENTS.md → `开始 (i)`。

### 5. (i) 的 4 个执行 step(下个会话直接照做)

1. `cp AGENTS.md CLAUDE.md` 或用 Write 工具整体覆盖 CLAUDE.md
2. 在 CLAUDE.md 和 AGENTS.md 的 `## 踩坑` 段末尾(`g1t03 跨容差` 那行之后、`## Compact 须知` 之前)同时追加 §2 的 A++ bullet
3. `bash .claude/scripts/check-agents-sync.sh` 必须 PASS,`wc -l CLAUDE.md` 应为 154
4. `git add CLAUDE.md AGENTS.md .pipeline/agent_handoff.md .pipeline/tasks.json .pipeline/research/precompact_hook_best_practices.md && git commit` 一次 commit 修两个问题(同时把今天的 PreCompact 调研产物 commit 进去)

### 6. 已做(本会话所有动作)

- 读了 `.claude/scripts/check-agents-sync.sh`(strict diff,exit 0/2)、`CLAUDE.md`、`AGENTS.md`
- 跑了 `bash .claude/scripts/check-agents-sync.sh`(exit=2)、`diff CLAUDE.md AGENTS.md`、`wc -l CLAUDE.md AGENTS.md`
- **零代码/文档修改**;追加了 5 条 handoff 条目(包括本条)

### 7. 工程纪律备注

- `tasks.json#impl-precompact-hook` 仍 todo,本会话不动(#26)
- `.pipeline/research/precompact_hook_best_practices.md` 仍未 commit,等本次一并
- `agent_handoff.md` 历史 MD032 警告(line 12/18/33/48/53)+ 本条可能新增的 MD037(line ~164)是旧问题/无关代码风格,**不要顺手清扫**
- 本会话 git status 应为:`M .pipeline/agent_handoff.md`、`M .pipeline/tasks.json`、`?? .pipeline/research/`(其他文件零修改)

## Handoff: 反向 sync + A++ 落地完成 — 2026-04-08

> 接续上一条"综合快照"。Dr Sun 选"换反向 sync"——CLAUDE.md 是权威(Dr Sun 已手动清理算法名称映射 / CSV 三层等他认为错误的段),AGENTS.md 反向抄 CLAUDE.md。**前一条卡点已解,本会话本任务收尾。**

### 1. 本会话完成的唯一一件事(守 #26)

1. `Edit CLAUDE.md` 在 `## 踩坑` 段末尾(`g1t03 跨容差` 之后、`## Compact 须知` 之前)插入 A++ bullet:
   > 子 agent(含 claude-code-guide)调用 prompt 必须强制其 WebFetch/Grep 真实源再答并附 URL + 原文片段。即便如此,LLM 仍会伪造与源不逐字对齐的"原文引号"(quote-fabrication 已知失败模式),所以主会话必须把引号字段与源 spot-check。结论性陈述若无引号,可信度高(硬规则 #12 的具体场景)。
2. `cp CLAUDE.md AGENTS.md`(整体覆盖,把 Dr Sun 的清理 + 新加 A++ 一次性反向 sync)
3. `bash .claude/scripts/check-agents-sync.sh` → ✅ PASS
4. `wc -l`:CLAUDE.md 139 / AGENTS.md 139(原 138 + A++ 1 行)

### 2. 硬规则 #23 状态

**已恢复 ≡**。前一条 handoff 列出的 7 处 diff 全部清零。CLAUDE.md 是权威这一方向是 Dr Sun 主动清理后的明确决定,不再需要"git 考古"。

### 3. 本会话 commit 顺序(2 个 commit)

- **Commit 1** `docs(workflow)`:`CLAUDE.md` + `AGENTS.md` + `.pipeline/research/precompact_hook_best_practices.md` + `.pipeline/tasks.json`(把上次 PreCompact 调研收尾产物 + 反向 sync + A++ 一并 commit)
- **Commit 2** `chore(handoff)`:`.pipeline/agent_handoff.md`(本条 + 上次 5 条 handoff)

### 4. 下一会话的任务

- `tasks.json#impl-precompact-hook`(medium / todo):落地 PreCompact 双轨方案
  - **轨 A**:`.claude/scripts/pre-compact.sh`(防 auto-compact,占位 handoff 兜底)
  - **轨 B**:`.claude/commands/compact-safe.md`(防 manual /compact,EmanuelFaria 自定义 instructions 模式)
  - 完整设计 + 限制 + 4 个候选方案对比见 `.pipeline/research/precompact_hook_best_practices.md` §3 + §4.2
  - **落地前 MUST**:跑 `claude --version` 确认是否仍是 #13572 受影响版本,然后跑一次 manual `/compact` 实测 PreCompact hook 是否触发

### 5. 工程纪律备注

- `agent_handoff.md` 历史 MD032/MD037 警告(含本条新增的若干 bullet/表格 markdown lint)是 markdownlint 风格遗留,**不要顺手清扫**(scope creep,#26 精神)
- 上次会话最初的 4 条 handoff(2 条等 Dr Sun 选 sync 方向、1 条 PreCompact 研究启动、1 条研究完成)是过程记录,可跳读
- 本条 + 上次的"综合快照"是当前 sync 解决路径的完整记录,**下一会话只需读本条 §4 即可定位下一任务**

## Handoff: 补记 push + memory 系统启用 — 2026-04-08

> 接续上一条"反向 sync + A++ 落地"。本次会话完整收尾的最后两步。

- `git push origin main`:`6018e12..cc7e876` fast-forward 推 2 commits 到远端,远端 history 与本地 ≡
- Dr Sun 授权"工作流文档 commit 也允许 push";已记入 memory `~/.claude/projects/.../memory/feedback_workflow_doc_push.md`,`MEMORY.md` 索引建立(此前 memory 目录为空)
- 下一会话:`tasks.json#impl-precompact-hook`(双轨方案,设计见 `.pipeline/research/precompact_hook_best_practices.md` §4.2)
