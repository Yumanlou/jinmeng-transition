#!/usr/bin/env python3
"""Create the main-text GEM asset-lifecycle figure for the Energy Policy draft.

The figure uses the retrospective province-year GEM lifecycle panel and reports
national sums.  It deliberately separates annual coal flows from operating
stocks so that renewable expansion is not mistaken for coal-asset exit.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/gem_power_project_lifecycle/gem_province_year_lifecycle_2000_2023.csv"
OUTDIR = ROOT / "result/figures/energy_policy_lockin_0820"
OUTBASE = OUTDIR / "Figure_1_asset_lifecycle"


def main() -> None:
    raw = pd.read_csv(INPUT)
    national = (
        raw.groupby("year", as_index=False)[
            [
                "gem_coal_new_mw",
                "gem_coal_retired_mw",
                "gem_coal_stock_mw",
                "gem_ws_stock_mw",
            ]
        ]
        .sum()
        .sort_values("year")
    )
    for column in national.columns[1:]:
        national[column] = national[column] / 1000
    national["gem_coal_net_new_mw"] = (
        national["gem_coal_new_mw"] - national["gem_coal_retired_mw"]
    )

    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, (ax_flow, ax_stock) = plt.subplots(
        2, 1, figsize=(7.1, 5.4), sharex=True, constrained_layout=True
    )
    years = national["year"].to_numpy()
    width = 0.72

    ax_flow.bar(
        years,
        national["gem_coal_new_mw"],
        width=width,
        color="#8C564B",
        label="Coal commissioned",
        zorder=2,
    )
    ax_flow.bar(
        years,
        -national["gem_coal_retired_mw"],
        width=width,
        color="#BDBDBD",
        label="Coal retired",
        zorder=2,
    )
    ax_flow.plot(
        years,
        national["gem_coal_net_new_mw"],
        color="#202020",
        linewidth=1.7,
        marker="o",
        markersize=2.8,
        label="Net coal addition",
        zorder=3,
    )
    ax_flow.axhline(0, color="#555555", linewidth=0.7)
    ax_flow.set_ylabel("GW per year")
    ax_flow.set_title("(a) Annual coal-capacity flows")
    ax_flow.grid(axis="y", color="#E6E6E6", linewidth=0.7, zorder=0)
    ax_flow.legend(loc="upper right", ncol=3, frameon=False, handlelength=1.7)

    ax_stock.plot(
        years,
        national["gem_coal_stock_mw"],
        color="#8C564B",
        linewidth=2.1,
        label="Coal operating stock (30 MW+)",
    )
    ax_stock.plot(
        years,
        national["gem_ws_stock_mw"],
        color="#2A9D8F",
        linewidth=2.1,
        label="Wind and solar operating stock",
    )
    for x in (2011, 2023):
        ax_stock.axvline(x, color="#BFBFBF", linestyle=":", linewidth=0.8, zorder=0)
    ax_stock.annotate(
        "Coal: 686 GW",
        xy=(2011, national.loc[national.year.eq(2011), "gem_coal_stock_mw"].iloc[0]),
        xytext=(2004.0, 760),
        arrowprops={"arrowstyle": "-", "color": "#8C564B", "lw": 0.8},
        color="#6D4037",
        fontsize=8,
    )
    ax_stock.annotate(
        "Coal: 1,143 GW",
        xy=(2023, national.loc[national.year.eq(2023), "gem_coal_stock_mw"].iloc[0]),
        xytext=(2015.3, 1170),
        arrowprops={"arrowstyle": "-", "color": "#8C564B", "lw": 0.8},
        color="#6D4037",
        fontsize=8,
    )
    ax_stock.annotate(
        "Wind + solar: 723 GW",
        xy=(2023, national.loc[national.year.eq(2023), "gem_ws_stock_mw"].iloc[0]),
        xytext=(2013.7, 670),
        arrowprops={"arrowstyle": "-", "color": "#2A9D8F", "lw": 0.8},
        color="#1E756B",
        fontsize=8,
    )
    ax_stock.set_ylabel("Operating capacity (GW)")
    ax_stock.set_xlabel("Year")
    ax_stock.set_title("(b) Reconstructed operating capacity")
    ax_stock.set_xlim(1999.4, 2023.6)
    ax_stock.set_ylim(-20, 1250)
    ax_stock.set_xticks([2000, 2004, 2008, 2012, 2016, 2020, 2023])
    ax_stock.grid(axis="y", color="#E6E6E6", linewidth=0.7, zorder=0)
    ax_stock.legend(loc="upper left", frameon=False)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTBASE.with_suffix(".pdf"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTBASE.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUTBASE.with_suffix('.pdf')}")
    print(f"Wrote {OUTBASE.with_suffix('.png')}")


if __name__ == "__main__":
    main()
