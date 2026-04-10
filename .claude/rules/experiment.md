---
paths: ["2_experiment/**", "configs/**"]
---

# 实验规则

## 硬规则

- MUST:所有训练/推理参数通过 `2_experiment/configs/*.json` 管理,代码改动须新增 `repro_YYYYMMDD_<topic>.json`(纯文档改动豁免)。
- MUST:消融实验结束后在 `2_experiment/runs/ablation_logs/` 写 `ablation_YYYYMMDD_<topic>.md`。
- MUST:远端训练前必须完整 `rsync` 同步代码(含 `2_experiment/`),严禁未同步就启动远端训练(无例外)。
- MUST:推理前必须确认 checkpoint 文件正确,不能依赖"默认最新"。
- MUST:SSH 远程执行 conda 必须 `conda run --cwd <项目绝对路径>/2_experiment -n ros2py310 python ...`(不 cd 会用错目录)。
- MUST:代码包名为 `ugv_dqn`(不是 `amr_dqn`),所有 import 使用 `from ugv_dqn.xxx import ...`。
- NEVER:SS-RRT* 专家引入任何 cost-to-go 泄漏或回退(Dr Sun 视为造假)。

## 环境

| 平台 | 用途 | Conda | 说明 |
| ---- | ---- | ----- | ---- |
| Mac (Apple Silicon) | 代码开发 / 论文写作 | `/opt/homebrew/Caskroom/miniforge/base` | PyTorch CPU 版,`KMP_DUPLICATE_LIB_OK=TRUE` 已设 |
| Ubuntu (远程 GPU) | 训练 + 推理 | `$HOME/miniconda3` | RTX 4090,环境 `ros2py310` |

## 远程服务器

| 优先级 | 名称 | Host | 用户 | GPU | 项目路径 |
| ------ | ---- | ---- | ---- | --- | -------- |
| 1 | uhost-1nwalbarw6ki | 117.50.216.203 | ubuntu | RTX 4090 (24GB) | `$HOME/DQN10/` |
| 2 | ubuntu-zt | (ZeroTier) | sun | — | 长期训练 + checkpoint 存档 |

连接方式优先 paramiko(本地无 sshpass)。凭证不写入 repo。

## 常用命令

```bash
PROJ=$HOME/DQN10; EXP=$PROJ/2_experiment; ENV=ros2py310

# 训练(后台)
nohup conda run --cwd $EXP -n $ENV python train.py --profile $PROFILE \
  > $EXP/runs/${PROFILE}_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 推理
conda run --cwd $EXP -n $ENV python infer.py --profile $PROFILE

# 自检
conda run --cwd $EXP -n $ENV python train.py --self-check
conda run --cwd $EXP -n $ENV python infer.py --self-check

# 完成判定
ls $EXP/runs/$RUN/train_*/infer/*/table2_kpis.csv 2>/dev/null && echo DONE || echo RUNNING
```

## 实验数据结构

数据链路:`2_experiment/configs/*.json` → `infer.py --profile <name>` → `2_experiment/runs*/infer/<out>/` 生成 CSV。

**SR 模式 vs Quality 模式**(禁止混用):

- **SR 模式**:BK 可达筛选,全量 50 runs,**仅汇报成功率**——对应 `table2_kpis_mean.csv`,config `filter_all_succeed: false`。
- **Quality 模式**:N-算法全成功筛选,runs 较少,成功率恒 100%,**仅汇报路径质量**——对应 `table2_kpis_mean_filtered.csv`,config `filter_all_succeed: true`。

**runs20260408_{dqn,ddqn}**:§4.5 cnn-dqn vs cnn-ddqn 底座消融数据(12 train + 24 infer),当前主要对比来源。
