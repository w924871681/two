from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper_figures"
DATA = PAPER / "data"
PDF = PAPER / "pdf"
PNG = PAPER / "png"
TABLES = PAPER / "tables"
AUDITS = PAPER / "audits"

METHOD_ORDER = ["RAVM-DT", "Always-FT", "ER", "EWC", "Huber-FT", "ValidationCommit", "Frozen"]
METHOD_MAP = {"Proposed": "RAVM-DT"}
COLORS = {
    # Muted categorical palette extracted from the first-paper baseline figure.
    "RAVM-DT": "#6E8FB3",
    "Always-FT": "#D9A25F",
    "ER": "#8DB8B0",
    "EWC": "#B39BBC",
    "Huber-FT": "#B79A62",
    "ValidationCommit": "#8F99A6",
    "Frozen": "#C6C2BD",
}
MARKERS = {"RAVM-DT": "o", "Always-FT": "s", "ER": "^", "EWC": "D", "Huber-FT": "v", "ValidationCommit": "P", "Frozen": "X"}
SCENARIO_COLORS = {
    "Mixed": "#6E8FB3",
    "Persistent bias": "#D9A25F",
    "Replay": "#8F99A6",
    "Clean": "#E7EDF1",
}
SCENARIO_MARKERS = {"Mixed": "o", "Persistent bias": "s", "Replay": "^", "Clean": "o"}
MECHANISM_COLORS = {
    "proposed": "#6E8FB3",
    "aggressive": "#D9A25F",
    "conservative": "#8F99A6",
    "harmful": "#C77979",
    "retained": "#C6C2BD",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_dirs() -> None:
    for path in [DATA, PDF, PNG, TABLES, AUDITS]:
        path.mkdir(parents=True, exist_ok=True)


def style() -> None:
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Tinos", "Times New Roman"],
        "mathtext.fontset": "stix",
        "font.size": 8.0,
        "axes.labelsize": 8.5,
        "axes.titlesize": 8.5,
        "xtick.labelsize": 7.2,
        "ytick.labelsize": 7.2,
        "legend.fontsize": 7.0,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def clean_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D7D7D7", linewidth=0.5, alpha=0.65, linestyle=(0, (1.5, 2.2)), zorder=0)
    ax.tick_params(direction="out")


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.13, 1.055, label, transform=ax.transAxes, fontweight="bold", fontsize=9, va="top")


def point_range(ax: plt.Axes, x: float, y: float, lo: float, hi: float, color: str, marker: str = "o", horizontal: bool = False, zorder: int = 3) -> None:
    kw = dict(fmt=marker, ms=4.3, mfc="white", mec=color, mew=0.9, ecolor=color, elinewidth=0.75, capsize=2.0, capthick=0.75, zorder=zorder)
    if horizontal:
        ax.errorbar(x, y, xerr=np.array([[x - lo], [hi - x]]), **kw)
    else:
        ax.errorbar(x, y, yerr=np.array([[y - lo], [hi - y]]), **kw)


def save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    ensure_dirs()
    pdf = PDF / f"{stem}.pdf"
    png = PNG / f"{stem}.png"
    fixed_pdf_metadata = {
        "Creator": "RAVM-DT deterministic figure pipeline",
        "Producer": "Matplotlib",
        "CreationDate": datetime(2000, 1, 1),
        "ModDate": datetime(2000, 1, 1),
    }
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.035, metadata=fixed_pdf_metadata)
    fig.savefig(png, dpi=600, bbox_inches="tight", pad_inches=0.035)
    plt.close(fig)
    return pdf, png


def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)
