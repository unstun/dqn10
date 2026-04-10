"""
generate_report.py
将 results/*.json 汇总为 report.md
目录摘要字段: maturity
"""

import json
import glob
import os
import yaml

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIELDS_PATH = os.path.join(BASE_DIR, "fields.yaml")
REPORT_PATH = os.path.join(BASE_DIR, "report.md")

# ------------------------------------------------------------------ #
#  字段分类映射 (fields.yaml key -> JSON 可能用的 key)
# ------------------------------------------------------------------ #
CATEGORY_MAPPING = {
    "basic":            ["basic", "基本信息", "basic_info"],
    "core_mechanism":   ["core_mechanism", "核心机制", "core"],
    "technical":        ["technical", "技术特性", "technical_features"],
    "practicality":     ["practicality", "实用性评估", "practicality_evaluation"],
    "research_fit":     ["research_fit", "科研适配", "research"],
    "uncertain":        ["uncertain", "uncertain_fields"],
}

INTERNAL_KEYS = {"uncertain", "uncertain_fields", "_source_file"}

# ------------------------------------------------------------------ #
#  工具函数
# ------------------------------------------------------------------ #

def slugify(name: str) -> str:
    """生成 Markdown 锚点."""
    return name.lower().replace(" ", "-").replace("/", "").replace("(", "").replace(")", "").replace(".", "")

def format_value(v) -> str:
    """将任意值格式化为可读字符串."""
    if v is None or v == "":
        return ""
    if isinstance(v, list):
        if not v:
            return ""
        if isinstance(v[0], dict):
            # list of dicts -> 每行一个 dict，kv 用 | 分隔
            lines = []
            for item in v:
                lines.append(" | ".join(f"{k}: {vv}" for k, vv in item.items()))
            return "\n".join(f"- {l}" for l in lines)
        return "、".join(str(x) for x in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}: {vv}" for k, vv in v.items())
    s = str(v)
    # 长文本换行
    if len(s) > 120:
        # 每 100 字符插入换行（不破坏词边界）
        s = s.replace("；", "；\n").replace("。", "。\n").replace("(", "\n(")
    return s

def get_field(data: dict, field_name: str):
    """从扁平或嵌套 JSON 中查找字段值."""
    # 1. 顶层直接命中
    if field_name in data:
        return data[field_name]
    # 2. 遍历嵌套 dict
    for k, v in data.items():
        if isinstance(v, dict) and field_name in v:
            return v[field_name]
    return None

def is_uncertain(data: dict, field_name: str) -> bool:
    """判断该字段是否不确定."""
    uncertain_list = data.get("uncertain", data.get("uncertain_fields", []))
    if field_name in uncertain_list:
        return True
    val = get_field(data, field_name)
    if val is not None and "[不确定]" in str(val):
        return True
    return False

def load_fields(fields_path: str):
    """读取 fields.yaml，返回有序字段列表 [(category_label, [field_dicts])]."""
    with open(fields_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    sections = []
    LABELS = {
        "basic":          "基本信息",
        "core_mechanism": "核心机制",
        "technical":      "技术特性",
        "practicality":   "实用性评估",
        "research_fit":   "科研适配",
    }
    for key, label in LABELS.items():
        if key in raw:
            sections.append((label, raw[key]))

    # uncertain 字段单独处理
    uncertain_defs = raw.get("uncertain", [])
    return sections, uncertain_defs

# ------------------------------------------------------------------ #
#  主流程
# ------------------------------------------------------------------ #

def main():
    # 读取字段定义
    sections, uncertain_defs = load_fields(FIELDS_PATH)

    # 读取所有 JSON
    json_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")))
    items = []
    for fp in json_files:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        d["_source_file"] = os.path.basename(fp)
        items.append(d)

    # 按 category 分组排序
    CATEGORY_ORDER = ["判定机制", "缓存工程", "MCP生态", "验证核查", "架构范式"]
    def sort_key(d):
        cat = get_field(d, "category") or ""
        for i, c in enumerate(CATEGORY_ORDER):
            if c in cat:
                return i
        return 99
    items.sort(key=sort_key)

    lines = []

    # ---- 标题 ----
    lines.append("# LLM 本地知识缓存系统调研报告\n")
    lines.append("> **主题**: LLM 本地知识缓存系统设计 — 通过本地验证知识库减少 LLM 幻觉  \n")
    lines.append("> **日期**: 2026-04-10  \n")
    lines.append("> **范围**: 2025-04 ~ 2026-04  \n")
    lines.append("> **调研项目数**: 27  \n\n")
    lines.append("---\n\n")

    # ---- 目录 ----
    lines.append("## 目录\n\n")
    current_cat = None
    for idx, d in enumerate(items, 1):
        name = get_field(d, "name") or d["_source_file"]
        cat  = get_field(d, "category") or "其他"
        maturity = get_field(d, "maturity") or "—"

        if cat != current_cat:
            lines.append(f"\n### {cat}\n\n")
            current_cat = cat

        anchor = slugify(name)
        lines.append(f"{idx}. [{name}](#{anchor}) — {maturity}  \n")

    lines.append("\n---\n\n")

    # ---- 详细内容 ----
    lines.append("## 详细调研结果\n\n")

    current_cat = None
    for d in items:
        name = get_field(d, "name") or d["_source_file"]
        cat  = get_field(d, "category") or "其他"

        if cat != current_cat:
            lines.append(f"\n---\n\n## {cat}\n\n")
            current_cat = cat

        anchor = slugify(name)
        lines.append(f"### {name}\n\n")

        # 按 section 输出字段
        for section_label, field_defs in sections:
            section_lines = []
            for fdef in field_defs:
                fname = fdef["name"]
                if is_uncertain(d, fname):
                    continue
                val = get_field(d, fname)
                if val is None or val == "" or val == []:
                    continue
                formatted = format_value(val)
                if not formatted.strip():
                    continue
                section_lines.append(f"**{fname}**: {formatted}\n\n")

            if section_lines:
                lines.append(f"#### {section_label}\n\n")
                lines.extend(section_lines)

        # uncertain 字段节
        uncertain_list = d.get("uncertain", d.get("uncertain_fields", []))
        if uncertain_list:
            lines.append("#### 待核实字段\n\n")
            for u in uncertain_list:
                lines.append(f"- {u}\n")
            lines.append("\n")

        # 额外字段（JSON 有但 fields.yaml 未定义）
        defined_fields = set()
        for _, fds in sections:
            for fd in fds:
                defined_fields.add(fd["name"])
        for udef in uncertain_defs:
            defined_fields.add(udef["name"])

        extras = {}
        for k, v in d.items():
            if k in INTERNAL_KEYS:
                continue
            if k in defined_fields:
                continue
            if isinstance(v, dict):  # 嵌套 category key，忽略
                continue
            extras[k] = v

        if extras:
            lines.append("#### 其他信息\n\n")
            for k, v in extras.items():
                lines.append(f"**{k}**: {format_value(v)}\n\n")

        lines.append("\n")

    # ---- 写出 ----
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"报告已写入: {REPORT_PATH}")
    print(f"共处理 {len(items)} 个 items")

if __name__ == "__main__":
    main()
