# Terminology (继承自 DQN9)

| 中文 | 英文 | 禁用 | 说明 |
|---|---|---|---|
| Dijkstra 目标距离图 | goal distance map | cost-to-go field/map、目标距离场 | Dijkstra 预计算的绕障最短路径距离图；"cost-to-go" 在 DRL 语境下与值函数混淆，禁用；"场" 改 "图" 以匹配论文用语 |
| MD | MHA + Duel | — | Multi-Head Attention + Dueling Network 组合简称 |

## 观测与奖励描述

- 观测通道：occupancy, **goal distance**
- 奖励塑形：potential function defined as the geodesic goal distance

## 论文写作硬约束（摘自 DQN9 CLAUDE.md）

- 禁止括号补充说明（缩写定义除外，如 "深度强化学习（DRL）"）；改用 "即""由…构成""如图…所示"
- 公式使用 $\Delta c$、$\delta$、$\epsilon$ 等标准数学符号，禁止 `grid_size` 等代码风格变量名
- 独立公式末尾不加标点
- 禁止 "张量""编码" 描述地图输入，用 "地图""记录"
- 方法论禁止 enumerate 列表式写法，须散文叙事
- 禁止 EDT 等实现层术语，用 "欧氏距离" 等数学概念
- 术语必须溯源文献，禁止捏造
