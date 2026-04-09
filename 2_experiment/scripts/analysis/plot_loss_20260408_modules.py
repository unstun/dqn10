#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# Plot training TD-loss curves for 4 module variants
# (base / duel / munch / munch_duel) x {dqn, ddqn}
# Excludes noAM / noDQfD component ablation variants.
# ============================================================
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs20260408_loss_plots"
OUT.mkdir(exist_ok=True)

VARIANTS = ["abl_8var_cnn_{b}", "abl_8var_cnn_{b}_duel",
            "abl_8var_cnn_{b}_munch", "abl_8var_cnn_{b}_munch_duel"]
LABELS = ["base", "+Duel", "+Munch", "+Duel+Munch"]
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

def load(base):
    root = ROOT / f"runs20260408_{base}" / "train"
    out = {}
    for v, lab in zip(VARIANTS, LABELS):
        d = root / v.format(b=base)
        run = sorted([p for p in d.glob("train_*") if p.is_dir()])[-1]
        csv = run / "training_diagnostics.csv"
        out[lab] = pd.read_csv(csv)
    return out

def smooth(s, w=50):
    return s.rolling(w, min_periods=1).mean()

def plot_one(data, base, ax):
    for (lab, df), c in zip(data.items(), COLORS):
        ax.plot(df["episode"], smooth(df["td_loss"]), label=lab, color=c, lw=1.2)
    ax.set_title(f"CNN-{base.upper()}  TD loss (smoothed w=50)")
    ax.set_xlabel("episode"); ax.set_ylabel("td_loss")
    ax.set_yscale("log"); ax.grid(alpha=0.3); ax.legend()

fig, ax = plt.subplots(figsize=(8, 5))
STYLES = {"dqn": "-", "ddqn": "--"}
for base in ["dqn", "ddqn"]:
    data = load(base)
    for (lab, df), c in zip(data.items(), COLORS):
        ax.plot(df["episode"], smooth(df["td_loss"]),
                color=c, ls=STYLES[base], lw=1.2,
                label=f"{base.upper()} {lab}")
ax.set_xlabel("episode"); ax.set_ylabel("td_loss (smoothed w=50)")
ax.set_yscale("log"); ax.grid(alpha=0.3)
ax.legend(ncol=2, fontsize=8)
ax.set_title("TD loss: CNN-DQN vs CNN-DDQN module ablation")
fig.tight_layout()
out = OUT / "td_loss_modules_combined.png"
fig.savefig(out, dpi=140)
print(out)
