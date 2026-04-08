#!/usr/bin/env python3
# ============================================================
# aggregate_20260408_raw.py
# 从 runs20260408_{dqn,ddqn}/infer/<variant>/<ts>/table2_kpis.csv
# 的原始 50-run 数据重新聚合，不依赖任何 mean/summary 文件。
# 输出: docs/agg_20260408_raw.md
# ============================================================
import csv
import re
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
BASES = {"dqn": ROOT / "runs20260408_dqn/infer",
         "ddqn": ROOT / "runs20260408_ddqn/infer"}

# variant name parsing:
# abl_amdqfd_cnn_{dqn|ddqn}[_munch][_duel]_infer_{full|noAM|noDQfD}_sr_{short|long}
PAT = re.compile(
    r"abl_amdqfd_cnn_(?:dqn|ddqn)(?P<munch>_munch)?(?P<duel>_duel)?"
    r"_infer_(?P<comp>full|noAM|noDQfD)_sr_(?P<dist>short|long)"
)

def parse(name):
    m = PAT.match(name)
    if not m:
        return None
    munch = bool(m.group("munch"))
    duel  = bool(m.group("duel"))
    arch = {(False, False): "plain",
            (False, True):  "Duel",
            (True,  False): "Munch",
            (True,  True):  "Munch+Duel"}[(munch, duel)]
    return arch, m.group("comp"), m.group("dist")

def load_runs(csv_path):
    rows = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

# {(base, arch, comp, dist): [row, ...]}
data = {}
for base, root in BASES.items():
    for d in sorted(root.iterdir()):
        parsed = parse(d.name)
        if not parsed:
            continue
        arch, comp, dist = parsed
        ts_dirs = [x for x in d.iterdir() if x.is_dir()]
        if not ts_dirs:
            continue
        csv_path = ts_dirs[0] / "table2_kpis.csv"
        if not csv_path.exists():
            continue
        data[(base, arch, comp, dist)] = load_runs(csv_path)

def sr_of(rows):
    # Success rate column is 0/1 per run
    vals = [float(r["Success rate"]) for r in rows]
    return mean(vals) if vals else float("nan")

def filtered_quality(rows_by_key, keys):
    # rows_by_key[k] = list of 50 rows; align by Run index;
    # keep only run indices where ALL keys succeed.
    if any(k not in rows_by_key for k in keys):
        return None
    per = {k: {int(r["Run index"]): r for r in rows_by_key[k]} for k in keys}
    common_idx = set.intersection(*[set(per[k].keys()) for k in keys])
    winners = sorted(i for i in common_idx
                     if all(float(per[k][i]["Success rate"]) == 1.0 for k in keys))
    if not winners:
        return None
    out = {}
    for k in keys:
        rs = [per[k][i] for i in winners]
        out[k] = {
            "N": len(rs),
            "len":  mean(float(r["Average path length (m)"]) for r in rs),
            "curv": mean(float(r["Average curvature (1/m)"]) for r in rs),
            "time": mean(float(r["Compute time (s)"]) for r in rs),
        }
    return out, len(winners)

ARCHES = ["plain", "Duel", "Munch", "Munch+Duel"]
COMPS  = ["full", "noAM", "noDQfD"]
BASES_ORDER = ["dqn", "ddqn"]
DISTS = ["short", "long"]

out = []
out.append("# 20260408 真实数据聚合（从 table2_kpis.csv 原始 50-run 重新算）\n")
out.append("未触碰 summary xlsx / mean csv。聚合脚本：scripts/aggregate_20260408_raw.py\n\n")

# ============================================================
# PART A: 结构头 — 固定 comp=full, 变 base × arch
# ============================================================
out.append("## A. 结构头 (固定 comp=full)\n")
out.append("### A.1 SR 模式 (原始 50 runs 均值)\n\n")
out.append("| base | arch | short SR | long SR |\n|---|---|---:|---:|\n")
for base in BASES_ORDER:
    for arch in ARCHES:
        s = data.get((base, arch, "full", "short"))
        l = data.get((base, arch, "full", "long"))
        out.append(f"| {base} | {arch} | "
                   f"{sr_of(s)*100:.0f}% | {sr_of(l)*100:.0f}% |\n"
                   if s and l else
                   f"| {base} | {arch} | N/A | N/A |\n")

for dist in DISTS:
    out.append(f"\n### A.2 结构头 Quality 模式 ({dist}, 按 base 分别 4-arch 全成功过滤)\n\n")
    out.append("| base | arch | N | path len (m) | curv (1/m) | compute (s) |\n"
               "|---|---|---:|---:|---:|---:|\n")
    for base in BASES_ORDER:
        rows_by_key = {arch: data.get((base, arch, "full", dist)) for arch in ARCHES}
        keys = [a for a in ARCHES if rows_by_key.get(a)]
        if len(keys) < 2:
            continue
        res = filtered_quality(rows_by_key, keys)
        if not res:
            out.append(f"| {base} | — | 0 | — | — | — |\n")
            continue
        stats, N = res
        for arch in keys:
            s = stats[arch]
            out.append(f"| {base} | {arch} | {N} | "
                       f"{s['len']:.3f} | {s['curv']:.4f} | {s['time']:.3f} |\n")

# ============================================================
# PART B: 模块头 — 变 base × comp, arch 枚举四种（先全给，后决定固定哪个）
# ============================================================
out.append("\n## B. 模块头 (枚举四种固定架构, 供选最优)\n")
for fixed_arch in ARCHES:
    out.append(f"\n### B.{fixed_arch} (固定 arch={fixed_arch})\n\n")
    out.append("#### SR 模式\n\n")
    out.append("| base | comp | short SR | long SR |\n|---|---|---:|---:|\n")
    for base in BASES_ORDER:
        for comp in COMPS:
            s = data.get((base, fixed_arch, comp, "short"))
            l = data.get((base, fixed_arch, comp, "long"))
            out.append(f"| {base} | {comp} | "
                       f"{sr_of(s)*100:.0f}% | {sr_of(l)*100:.0f}% |\n"
                       if s and l else
                       f"| {base} | {comp} | N/A | N/A |\n")
    for dist in DISTS:
        out.append(f"\n#### Quality 模式 ({dist}, 按 base 分别 3-comp 全成功过滤)\n\n")
        out.append("| base | comp | N | path len (m) | curv (1/m) | compute (s) |\n"
                   "|---|---|---:|---:|---:|---:|\n")
        for base in BASES_ORDER:
            rows_by_key = {comp: data.get((base, fixed_arch, comp, dist)) for comp in COMPS}
            keys = [c for c in COMPS if rows_by_key.get(c)]
            if len(keys) < 2:
                continue
            res = filtered_quality(rows_by_key, keys)
            if not res:
                out.append(f"| {base} | — | 0 | — | — | — |\n")
                continue
            stats, N = res
            for comp in keys:
                s = stats[comp]
                out.append(f"| {base} | {comp} | {N} | "
                           f"{s['len']:.3f} | {s['curv']:.4f} | {s['time']:.3f} |\n")

# Sanity: check data coverage
out.append("\n## 数据覆盖检查\n\n")
expected = len(BASES_ORDER) * len(ARCHES) * len(COMPS) * len(DISTS)
got = len(data)
out.append(f"期望 {expected} 组，实际读到 {got} 组。\n")
if got != expected:
    missing = [(b, a, c, d) for b in BASES_ORDER for a in ARCHES
               for c in COMPS for d in DISTS
               if (b, a, c, d) not in data]
    out.append(f"缺失: {missing}\n")

OUT = ROOT / "docs" / "agg_20260408_raw.md"
OUT.parent.mkdir(exist_ok=True)
OUT.write_text("".join(out))
print(f"wrote {OUT}")
