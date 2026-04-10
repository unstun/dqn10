# 踩坑集合

- WebFetch 与 WebSearch 不混在同一批并行调用(WebFetch 403 会级联拖垮同批 WebSearch),每批并行最多 2 个同类调用。
- PDF 链接大概率解析失败,优先 HTML 版本(如 `arxiv.org/html/`)。
- `conda run` 不会自动 cd,必须 `--cwd <绝对路径>`。
- 远端 `~/.bashrc` 的 conda init 块必须放在 interactive guard (`case $- in`) 之前。
- LaTeX:`xelatex` 支持中文注释,提交版用 `pdflatex`,缺包 `sudo tlmgr install <pkg>`。
- argparse 默认 `forest_baseline_rollout=True`,config 必须显式写 `forest_baseline_rollout: false` 才能关 MPC。
- g1t03 跨容差(train 1.0m + infer 0.3m)是设计如此,不要误判为错误。
- 子 agent(含 claude-code-guide)调用 prompt 必须强制其 WebFetch/Grep 真实源再答并附 URL + 原文片段。LLM 仍会伪造"原文引号"(quote-fabrication 已知失败模式),主会话必须 spot-check 引号字段。
