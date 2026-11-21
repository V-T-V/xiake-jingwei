# -*- coding: utf-8 -*-
"""霞客经纬 · 论文插图生成：python tools/build_paper_figs.py

数据源（口径纪律）：docs/stats.json（tools/build_stats.py 产物）——凡数字出自脚本。
输出：docs/figs/fig1_trips.png · fig2_years.png（200dpi 绢底绛霞，学 HHH docs/build_paper_figs.py）
build_paper_pdf.py 于插图缺失时自动调用本脚本（管线可重入）。
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "figs")
os.makedirs(OUT, exist_ok=True)

STATS = json.load(open(os.path.join(ROOT, "docs", "stats.json"), encoding="utf-8"))

# ── 绢底绛霞版式（沿站点 css 与 PDF 配色） ──
SILK, INK, MUTED = "#f5f2e3", "#2e2a26", "#8d8177"
CINNABAR, GRIDC = "#8e2b22", "#ddd6c2"
plt.rcParams.update({
    "font.family": "Microsoft YaHei", "axes.unicode_minus": False,
    "figure.facecolor": SILK, "axes.facecolor": SILK,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
})
KAI = FontProperties(fname=r"C:\Windows\Fonts\simkai.ttf", size=14)


def frame(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="x", color=GRIDC, lw=.7, alpha=.8)
    ax.set_axisbelow(True)


# ══ 图 1　廿二程日条长短：短游与长程的双态 ══
trips = STATS["trips"]                       # stats.json:trips（title/year/days）
fig, ax = plt.subplots(figsize=(7.2, 5.4), dpi=200)
frame(ax)
names = [t["title"] for t in trips][::-1]
days = [t["days"] for t in trips][::-1]
cols = [CINNABAR if t["year"].startswith("163") and int(t["year"][:4]) >= 1636 else MUTED
        for t in trips][::-1]
ax.barh(names, days, color=cols, height=.66, edgecolor=SILK, lw=.5)
for i, d in enumerate(days):
    ax.text(d + 1.5, i, str(d), va="center", fontsize=8, color=INK)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=8.5)
ax.set_xlabel("日条数", fontsize=9.5)
ax.set_xlim(0, max(days) * 1.14)
ax.set_title("廿二程日条长短：早年短游与晚年长程的双态", fontproperties=KAI, pad=12)
ax.legend(handles=[Patch(fc=CINNABAR, label="万里遐征段（1636–1637）"),
                   Patch(fc=MUTED, label="早年诸游（1613–1633）")],
          loc="lower right", fontsize=8.5, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_trips.png"))
plt.close(fig)

# ══ 图 2　游年分布：晚年西行为全书重心 ══
years = STATS["years"]                       # stats.json:years（[年, 日条]）
last2 = sum(y[1] for y in years[-2:])
pct = round(last2 / STATS["meta"]["days"] * 100)
fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", color=GRIDC, lw=.7, alpha=.8)
ax.set_axisbelow(True)
xs = [str(y[0]) for y in years]
ys = [y[1] for y in years]
cols = [MUTED] * len(xs)
cols[-2], cols[-1] = CINNABAR, CINNABAR
ax.bar(xs, ys, color=cols, width=.62, edgecolor=SILK, lw=.5)
for i, v in enumerate(ys):
    ax.text(i, v + 4, f"{v}", ha="center", fontsize=8.5, color=INK)
ax.set_ylabel("日条数", fontsize=9.5)
ax.set_ylim(0, max(ys) * 1.16)
ax.set_title(f"游年分布（10 个游年）——1636–1637「万里遐征」{last2} 日条占 {pct}%",
             fontproperties=KAI, pad=12)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_years.png"))
plt.close(fig)

print("OK →", OUT, sorted(os.listdir(OUT)))
