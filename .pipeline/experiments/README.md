# 实验台账

每轮实验一个文件,命名 `YYYYMMDD_<topic>.md`。

## 单文件格式

```markdown
# [实验主题]
> 日期：YYYY-MM-DD | Config: `configs/<name>.json`

## 目的
[这轮实验要验证什么]

## 设置
- Run 目录: `runs/<dir>/`
- 模式: SR / Quality
- 训练轮次 / 推理 runs 数

## 结果
[关键指标,表格或数值]

## 结论
[实验结论,是否支持假设]
```
