# DQN10 研究项目

> 继承自 DQN9 的算法/论文硬规则 + 机器狗RL 的 Conductor/Worker 会话协议。
> `CLAUDE.md ≡ AGENTS.md`(逐行一致,见硬规则 #23)。
> 作用域:`/Users/sun/tongbu/study/phdproject/dqn/DQN10/**` (Mac)、`$HOME/DQN10/**` (Ubuntu GPU)。

## 你是谁

你在一个长周期 PhD 研究项目中工作。每次会话只做一件事。
会话协议:读状态 → 做一个任务 → 写状态 → 结束。

## 会话启动

1. Dr Sun 提出第一句话后,**自动**派 memory-worker 子 agent 从 bigmemory 全局抓取与问题相关的上下文
2. 基于返回的上下文 + 如需任务列表读 `.pipeline/tasks.json`
3. 开始工作

如果 `.pipeline/project_truth.md` 未填充,说明项目未初始化。请先与 Dr Sun 确认研究主题再开始。

## 项目分层（Harness）

`bigmemory/`、`.pipeline/`、`.factory/`、`.claude/`、`CLAUDE.md`/`AGENTS.md` 以及 `scripts/` 统称 Harness——项目无关的研究脚手架,可跨项目复用,与 DQN 算法本身无关。修改 Harness 文件时须保持双平台对齐(硬规则 #23)。

## 记忆地图

**bigmemory/(按需拉取,透明读写)**:

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

**记忆检索模型**: Droid 派 memory-worker(gpt-5.4);Claude Code 用 `--model sonnet` 或直接 Read。

**.pipeline/(研究专用)**:

- `project_truth.md` — 研究主题、假设、方法(只读,除非你是 Conductor)
- `tasks.json` — 任务列表
- `terminology.md` — 术语规范表(中英文术语、禁用词)
- `papers/` — 论文 PDF 本地副本(命名 `<CitationKey>.pdf`,付费墙补充材料加 `_supp` 后缀)

## 角色

- **Conductor**:规划方向、审查结果、更新 project_truth、管理 tasks.json
- **Worker**:执行具体任务(实验/文献/写作)

## 硬规则(MUST/NEVER)

1. MUST:每次回复以"Dr Sun,"开头。
2. MUST:默认中文回复,思考语言为专业流英语,交互与注释语言为中文。
3. MUST:注释须 ASCII 风格分块,代码如顶级开源库作品——"代码是写给人看的,只是顺便让机器运行"。
4. MUST:论文正文先中文写作,定稿后统一英文润色,README 等项目文档也用中文。
5. MUST:改文件前输出 3–7 步计划 + 文件清单 + 风险 + 验证,等"开始"后再动手。
6. MUST:Dr Sun 第一句话后,自动派 memory-worker(Droid: gpt-5.4 / Claude Code: sonnet)从 bigmemory 全局检索相关上下文,不等用户要求。
7. MUST:每完成一个有意义的变更就 git commit。
8. MUST:修改代码或论文文件前,先 `git add . && git commit && git push`,确保远端有可回退快照(无例外)。
9. MUST:bigmemory 冷区按天文件只追加不覆写,热区全量重写且须遵守容量预算(见 `bigmemory/格式规范.md`)。
10. MUST:文献 PDF / 数据集 / 实验产物 NEVER 保存到 `/tmp`,必须保存到项目内(论文 PDF → `.pipeline/papers/<CitationKey>.pdf`)。
11. MUST:遇到不确定的研究决策、技术选型、实验设计时,先问 Dr Sun 而不是自行决定。
12. MUST:专业问题先联网搜索(GitHub / arXiv / 官方文档)或本地文献核实后再答,禁止凭 AI 记忆,不确定的标注不确定。
13. MUST:学术问题必须先读 `paper/main.tex` 及相关章节,基于实际内容回答。
14. MUST:引用核查四步——`search_web` / Semantic Scholar 定位 → DOI 2 源确认 → `curl -LH "Accept: application/x-bibtex" https://doi.org/<DOI>` → 确认 claim 存在,失败标 `[CITATION NEEDED]`,严禁凭记忆生成 BibTeX。
15. MUST:代码搜索优先使用 ACE(`mcp__augment-context-engine__codebase-retrieval`)做语义理解,`Grep` 用于精确匹配,禁用 Bash 调 grep/rg,ACE 报错即回退到 Grep + Glob 不阻塞流程。
16. MUST:所有训练/推理参数通过 `configs/*.json` 管理,代码改动须在 `configs/` 新增 `repro_YYYYMMDD_<topic>.json`(纯文档改动豁免)。
17. MUST:消融实验结束后在 `runs/ablation_logs/` 写 `ablation_YYYYMMDD_<topic>.md`。
18. MUST:远端训练前必须完整 `rsync` 同步代码(含 `configs/`、`ugv_dqn/`、`scripts/`),严禁未同步就启动远端训练(无例外)。
19. MUST:推理前必须确认 checkpoint 文件正确,不能依赖"默认最新"。
20. MUST:复杂任务(多文件修改、跨模块调研、论文+代码联动)默认启用多 Agent 并行,简单单文件任务无需启用。
21. MUST:联网使用 Playwright MCP,付费墙站点(tandfonline / sciencedirect / springer)走 `browser_navigate` → `browser_wait_for 5s` → `browser_snapshot`。
22. MUST:SSH 远程执行 conda 必须 `conda run --cwd <项目绝对路径> -n ros2py310 python ...`(不 cd 会用错目录)。
23. MUST:`CLAUDE.md ≡ AGENTS.md`(逐行一致),修改任一文件后必须同步另一个,并跑 `bash .claude/scripts/check-agents-sync.sh` 验证。
24. MUST:`CLAUDE.md` / `AGENTS.md` 的受众是 AI,内容以 AI 可解析、可执行为优先;其余一切产出——论文、README、日志、bigmemory、以及主 AI 对 Dr Sun 的回复与提问——以人可读为优先。
25. MUST:代码包名为 `ugv_dqn`(不是 `amr_dqn`),所有 import 使用 `from ugv_dqn.xxx import ...`。
26. MUST:论文润色工作流——多 Agent 并行搜同领域真实句子 → 提炼句式特征 → 按句式改写并标注对标原句 → 自检删掉是否丢失信息。
27. NEVER:在一个会话里串联多个任务。
28. NEVER:修改 `project_truth.md`(除非当前角色是 Conductor)。
29. NEVER:同一时间有两个 Claude Code 会话操作本项目。
30. NEVER:论文中使用括号补充说明(缩写定义除外,如"深度强化学习(DRL)"),改用"即""由…构成""如图…所示"。
31. NEVER:公式中使用 `grid_size` 等代码风格变量名,须用 $\Delta c$、$\delta$、$\epsilon$ 等标准记法,独立公式末尾不加标点。
32. NEVER:论文中出现"张量""编码"描述地图输入,用"地图""记录"替代,禁用 EDT 等实现层术语,用"欧氏距离"等数学概念。
33. NEVER:论文方法论写 enumerate 列表式段落,须散文叙事。
34. NEVER:捏造术语、过度包装简单概念、使用推销性语言,术语须溯源文献。
35. NEVER:用户质疑时盲目顺从,必须回查原文事实后再回应,禁止放弃正确判断。
36. NEVER:SS-RRT* 专家引入任何 cost-to-go 泄漏或回退(Dr Sun 视为造假)。

## 环境

| 平台                | 用途                | Conda                                     | 说明                                                 |
| ------------------- | ------------------- | ----------------------------------------- | ---------------------------------------------------- |
| Mac (Apple Silicon) | 代码开发 / 论文写作 | `/opt/homebrew/Caskroom/miniforge/base` | PyTorch 为 CPU 版,`KMP_DUPLICATE_LIB_OK=TRUE` 已设 |
| Ubuntu (远程 GPU)   | 训练 + 推理         | `$HOME/miniconda3`                      | RTX 4090,环境 `ros2py310`                          |

## 远程服务器

| 优先级 | 名称               | Host           | 用户   | GPU             | 项目路径                   |
| ------ | ------------------ | -------------- | ------ | --------------- | -------------------------- |
| 1      | uhost-1nwalbarw6ki | 117.50.216.203 | ubuntu | RTX 4090 (24GB) | `$HOME/DQN10/`           |
| 2      | ubuntu-zt          | (ZeroTier)     | sun    | —              | 长期训练 + checkpoint 存档 |

连接方式优先 paramiko(本地无 sshpass)。凭证不写入 repo,见 `.pipeline/project_truth.md` 机密区。

## 常用命令

```bash
PROJ=$HOME/DQN10; ENV=ros2py310

# 训练(后台)
nohup conda run --cwd $PROJ -n $ENV python train.py --profile $PROFILE \
  > runs/${PROFILE}_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 推理
conda run --cwd $PROJ -n $ENV python infer.py --profile $PROFILE

# 自检
conda run --cwd $PROJ -n $ENV python train.py --self-check
conda run --cwd $PROJ -n $ENV python infer.py --self-check

# 完成判定
ls $PROJ/runs/$EXP/train_*/infer/*/table2_kpis.csv 2>/dev/null && echo DONE || echo RUNNING
```

## 实验数据结构(必读)

数据链路:`configs/*.json` → `infer.py --profile <name>` → `runs*/infer/<out>/` 生成 CSV。

**SR 模式 vs Quality 模式**(禁止混用):

- **SR 模式**:BK 可达筛选,全量 50 runs,**仅汇报成功率**——对应 `table2_kpis_mean.csv`,config 参数 `filter_all_succeed: false`。
- **Quality 模式**:N-算法全成功筛选,runs 较少(Long ~5–12, Short ~17–30),成功率恒为 100%,**仅汇报路径质量**(长度、曲率、计算时间)——对应 `table2_kpis_mean_filtered.csv`,config 参数 `filter_all_succeed: true`。

**runs20260408_{dqn,ddqn}**:§4.5 cnn-dqn vs cnn-ddqn 底座消融数据(12 train + 24 infer),当前主要对比来源。

## 踩坑

- WebFetch 与 WebSearch 不混在同一批并行调用(WebFetch 403 会级联拖垮同批 WebSearch),每批并行最多 2 个同类调用。
- PDF 链接大概率解析失败,优先 HTML 版本(如 `arxiv.org/html/`)。
- `conda run` 不会自动 cd,必须 `--cwd <绝对路径>`。
- 远端 `~/.bashrc` 的 conda init 块必须放在 interactive guard (`case $- in`) 之前。
- LaTeX:`xelatex` 支持中文注释,提交版用 `pdflatex`,缺包 `sudo tlmgr install <pkg>`。
- argparse 默认 `forest_baseline_rollout=True`,config 必须显式写 `forest_baseline_rollout: false` 才能关 MPC。
- g1t03 跨容差(train 1.0m + infer 0.3m)是设计如此,不要误判为错误。
- 子 agent(含 claude-code-guide)调用 prompt 必须强制其 WebFetch/Grep 真实源再答并附 URL + 原文片段。即便如此,LLM 仍会伪造与源不逐字对齐的"原文引号"(quote-fabrication 已知失败模式),所以主会话必须把引号字段与源 spot-check。结论性陈述若无引号,可信度高(硬规则 #12 的具体场景)。

## 记忆系统(bigmemory)

**入口(自动)**:Dr Sun 第一句话后,主 AI 自动派 memory-worker 从 bigmemory 抓取相关上下文。
- Droid:Task tool 派 memory-worker(gpt-5.4,read-only)
- Claude Code:`claude -p --model sonnet` 或直接 Read/Grep
- memory-worker 看不到 CLAUDE.md,它的 prompt 在 `.factory/droids/memory-worker.md`

**出口(手动)**:Dr Sun 在对话中调用 `/archive`,主 AI 按指令执行分诊 + 冷区归档 + 热区刷新。
- 归档完全由 Dr Sun 自主决定,无 hook 强制
- 所有写入在对话中透明进行(用户可见)

## Compact 须知

IMPORTANT:如果 context 使用过半,建议先调用 `/archive` 归档当前进度。
compact 前归档落盘后不受 compact 影响。
