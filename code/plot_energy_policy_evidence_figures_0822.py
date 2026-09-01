#!/usr/bin/env python3
"""Create Figures 2--4 for the Energy Policy coal-lock-in manuscript.

All figures are descriptive or observational displays.  They separate direct
asset evidence from the policy-diagnostic constraint profile and never treat
the province-level patterns as identified causal mechanisms.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter


ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "result/figures/energy_policy_lockin_0820"
GEM_UNITS = ROOT / "data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv"
LIFECYCLE = ROOT / "data/gem_power_project_lifecycle/gem_province_year_lifecycle_2000_2023.csv"
PANEL = ROOT / "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_0721.csv"
COX = ROOT / "result/tables/0820_coal_retirement_survival_final/period_specific_cox.csv"

EXCLUDE = {"cancelled", "construction", "announced", "shelved", "permitted", "pre-permit", "mothballed"}
COLORS = {"coal": "#8C564B", "renewable": "#2A9D8F", "retired": "#BDBDBD", "ink": "#202020"}


def style() -> None:
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


def save(fig: plt.Figure, stem: str) -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".pdf", ".png"):
        fig.savefig(OUTDIR / f"{stem}{suffix}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def load_exposure() -> dict[str, float]:
    exposure: dict[str, float] = {}
    with PANEL.open(encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            try:
                exposure[row["province"]] = float(row["coalexp_pre"])
            except (KeyError, TypeError, ValueError):
                continue
    return exposure


def post_2012_cohort() -> pd.DataFrame:
    """Return units operating at the start of 2012 for descriptive KM curves."""
    exposure = load_exposure()
    rows: list[dict[str, object]] = []
    with GEM_UNITS.open(encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            if row.get("asset") != "coal" or row.get("status") in EXCLUDE:
                continue
            try:
                start = float(row["start_year"])
            except (KeyError, TypeError, ValueError):
                continue
            province = row.get("province")
            if province not in exposure or start >= 2012:
                continue
            try:
                retired = float(row["retired_year"]) if row.get("retired_year") else None
            except ValueError:
                continue
            if retired is not None and retired < 2012:
                continue
            rows.append(
                {
                    "province": province,
                    "coal_exposure": exposure[province],
                    "duration": (retired if retired is not None and retired <= 2025 else 2026.0) - 2012.0,
                    "event": int(retired is not None and 2012 <= retired <= 2025),
                }
            )
    cohort = pd.DataFrame(rows)
    threshold = pd.Series(exposure).median()
    cohort["group"] = np.where(cohort["coal_exposure"] >= threshold, "High coal exposure", "Low coal exposure")
    return cohort


def plot_retirement_evidence() -> None:
    cohort = post_2012_cohort()
    cox = pd.read_csv(COX, encoding="utf-8-sig")
    cox = cox.loc[cox["specification"].eq("standardized_continuous")].copy()
    labels = {
        "pre_2000_2011": "2000--2011",
        "early_2012_2015": "2012--2015",
        "supply_2016_2020": "2016--2020",
        "carbon_2021_2025": "2021--2025",
    }
    cox["label"] = cox["period"].map(labels)
    cox["lower"] = np.exp(cox["coef"] - 1.96 * cox["se_cluster_province"])
    cox["upper"] = np.exp(cox["coef"] + 1.96 * cox["se_cluster_province"])

    fig, (ax_km, ax_hr) = plt.subplots(1, 2, figsize=(7.1, 3.35), constrained_layout=True)
    for group, color in (("High coal exposure", COLORS["coal"]), ("Low coal exposure", COLORS["renewable"])):
        sample = cohort.loc[cohort["group"].eq(group)]
        fitted = KaplanMeierFitter().fit(sample["duration"], event_observed=sample["event"])
        ax_km.step(
            fitted.survival_function_.index,
            1 - fitted.survival_function_.iloc[:, 0],
            where="post",
            color=color,
            linewidth=2,
            label=f"{group} (n={len(sample):,})",
        )
    ax_km.set_xlim(0, 14)
    ax_km.set_ylim(0, max(0.08, ax_km.get_ylim()[1]))
    ax_km.set_xlabel("Years since 2012")
    ax_km.set_ylabel("Cumulative retirement probability")
    ax_km.set_title("(a) 2012 operating cohort")
    ax_km.grid(axis="y", color="#E6E6E6", linewidth=0.7)
    ax_km.legend(frameon=False, loc="upper left")

    y = np.arange(len(cox))
    ax_hr.errorbar(
        cox["hazard_ratio"],
        y,
        xerr=np.vstack((cox["hazard_ratio"] - cox["lower"], cox["upper"] - cox["hazard_ratio"])),
        fmt="o",
        color=COLORS["ink"],
        ecolor=COLORS["ink"],
        elinewidth=1.2,
        capsize=3,
        markersize=5,
        zorder=3,
    )
    ax_hr.axvline(1, color="#777777", linestyle="--", linewidth=0.9)
    ax_hr.set_yticks(y, cox["label"])
    ax_hr.set_xlabel("Hazard ratio per 1-SD coal exposure")
    ax_hr.set_title("(b) Period-specific Cox estimates")
    ax_hr.set_xlim(0.45, 2.05)
    ax_hr.grid(axis="x", color="#E6E6E6", linewidth=0.7)
    ax_hr.invert_yaxis()
    save(fig, "Figure_2_retirement_evidence")


def plot_constraint_typology() -> None:
    panel = pd.read_csv(PANEL, low_memory=False)
    profile = (
        panel.loc[panel["year"].between(2020, 2023)]
        .groupby("province", as_index=False)
        .agg(
            coal_stock_mw=("gem_coal_stock_mw", "mean"),
            renewable_consumption_share=("renewable_consumption_share", "mean"),
            resource_dependence=("resource_dependence_index_pre0811", "mean"),
        )
    )
    profile["coal_stock_gw"] = profile["coal_stock_mw"] / 1000
    x_mid = profile["coal_stock_gw"].median()
    y_mid = profile["renewable_consumption_share"].median()
    labels = {"Shanxi", "Neimenggu", "Xinjiang", "Ningxia"}

    fig, ax = plt.subplots(figsize=(7.1, 4.45), constrained_layout=True)
    points = ax.scatter(
        profile["coal_stock_gw"],
        profile["renewable_consumption_share"] * 100,
        c=profile["resource_dependence"],
        cmap="RdYlBu_r",
        vmin=-1.05,
        vmax=3.1,
        s=55,
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
    )
    ax.axvline(x_mid, color="#8A8A8A", linestyle="--", linewidth=0.9)
    ax.axhline(y_mid * 100, color="#8A8A8A", linestyle="--", linewidth=0.9)
    for _, row in profile.loc[profile["province"].isin(labels)].iterrows():
        name = "Inner Mongolia" if row["province"] == "Neimenggu" else row["province"]
        offset = {"Shanxi": (4, 5), "Inner Mongolia": (-78, 6), "Xinjiang": (4, -11), "Ningxia": (4, 5)}[name]
        ax.annotate(name, (row["coal_stock_gw"], row["renewable_consumption_share"] * 100), xytext=offset, textcoords="offset points", fontsize=8)
    ax.set_xlim(-3, 106)
    ax.set_ylim(14, 94)
    ax.set_xlabel("Mean reconstructed coal operating stock, 2020--2023 (GW)")
    ax.set_ylabel("Mean renewable-consumption share, 2020--2023 (%)")
    ax.set_title("Provincial transition-constraint profile")
    ax.grid(color="#E6E6E6", linewidth=0.7, zorder=0)
    colorbar = fig.colorbar(points, ax=ax, pad=0.02)
    colorbar.set_label("Pre-policy resource-dependence index (standardized)")
    save(fig, "Figure_3_constraint_typology")


def plot_case_lifecycles() -> None:
    data = pd.read_csv(LIFECYCLE)
    cases = [("Shanxi", "Shanxi"), ("Neimenggu", "Inner Mongolia")]
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.25), sharex=True, constrained_layout=True)
    fig.set_constrained_layout_pads(wspace=0.13, hspace=0.13)
    for col, (code, title) in enumerate(cases):
        subset = data.loc[data["province"].eq(code)].sort_values("year").copy()
        years = subset["year"].to_numpy()
        new = subset["gem_coal_new_mw"].to_numpy() / 1000
        retired = subset["gem_coal_retired_mw"].to_numpy() / 1000
        stock = subset["gem_coal_stock_mw"].to_numpy() / 1000
        windsolar = subset["gem_ws_stock_mw"].to_numpy() / 1000
        flow = axes[0, col]
        flow.bar(years, new, width=0.72, color=COLORS["coal"], label="Coal commissioned", zorder=2)
        flow.bar(years, -retired, width=0.72, color=COLORS["retired"], label="Coal retired", zorder=2)
        flow.axhline(0, color="#555555", linewidth=0.7)
        flow.set_title(f"({chr(97 + col)}) {title}: annual coal-capacity flows")
        flow.set_ylim(-3, 14)
        flow.grid(axis="y", color="#E6E6E6", linewidth=0.7, zorder=0)
        if col == 0:
            flow.set_ylabel("GW per year")
        stock_ax = axes[1, col]
        stock_ax.plot(years, stock, color=COLORS["coal"], linewidth=2, label="Coal operating stock")
        stock_ax.plot(years, windsolar, color=COLORS["renewable"], linewidth=2, label="Wind and solar operating stock")
        stock_ax.axvline(2012, color="#BFBFBF", linestyle=":", linewidth=0.8)
        stock_ax.set_title(f"({chr(99 + col)}) {title}: operating capacity", fontsize=9.5, pad=7)
        stock_ax.set_ylim(-2, 130)
        stock_ax.grid(axis="y", color="#E6E6E6", linewidth=0.7, zorder=0)
        if col == 0:
            stock_ax.set_ylabel("Operating capacity (GW)")
        stock_ax.set_xlabel("Year")
        stock_ax.set_xticks([2000, 2006, 2012, 2018, 2023])
    axes[0, 0].legend(frameon=False, loc="upper left")
    axes[1, 0].legend(frameon=False, loc="upper left")
    save(fig, "Figure_4_case_lifecycles")


def plot_annual_composition_shares() -> None:
    """Plot national aggregate shares, preserving the relevant denominator per panel."""
    panel = pd.read_csv(PANEL, low_memory=False)
    energy_components = {
        "Coal": "coal_consumption_10k_tce_approx",
        "Oil products": "oil_consumption_10k_tce_approx",
        "LPG": "lpg_consumption_10k_tce_approx",
        "Natural gas": "gas_consumption_10k_tce_approx",
        "Electricity": "electricity_consumption_10k_tce_approx",
    }
    final_energy = panel.loc[panel["year"].between(2006, 2022), ["year", *energy_components.values()]].copy()
    annual_energy = final_energy.groupby("year", as_index=True).sum()
    annual_energy = annual_energy.div(annual_energy.sum(axis=1), axis=0) * 100
    annual_energy = annual_energy.rename(columns={value: key for key, value in energy_components.items()})

    power = panel.loc[panel["year"].between(2006, 2023)].copy()
    capacity = power.groupby("year")[["thermal_capacity_10k_kw", "total_capacity_10k_kw"]].sum()
    capacity["Thermal"] = 100 * capacity["thermal_capacity_10k_kw"] / capacity["total_capacity_10k_kw"]
    capacity["Non-thermal"] = 100 - capacity["Thermal"]
    generation = power.groupby("year")[["thermal_generation_billion_kwh", "total_generation_billion_kwh"]].sum()
    generation["Thermal"] = 100 * generation["thermal_generation_billion_kwh"] / generation["total_generation_billion_kwh"]
    generation["Non-thermal"] = 100 - generation["Thermal"]

    component_colors = {
        "Coal": "#8C564B",
        "Oil products": "#D99058",
        "LPG": "#CAB2D6",
        "Natural gas": "#5AA6B5",
        "Electricity": "#E6C65B",
    }
    # The power-panel legends sit to the right so they do not collide with the
    # panel titles when the figure is embedded at manuscript width.
    fig, axes = plt.subplots(3, 1, figsize=(8.25, 6.6), constrained_layout=True)
    bar_width = 0.78
    x_energy = np.arange(len(annual_energy))
    bottom = np.zeros(len(annual_energy))
    for name in energy_components:
        axes[0].bar(x_energy, annual_energy[name], bottom=bottom, width=bar_width, color=component_colors[name], label=name)
        bottom += annual_energy[name].to_numpy()
    axes[0].set_title("(a) Final-use energy composition")
    axes[0].set_ylabel("Share of five-energy final use (%)")
    axes[0].set_ylim(0, 100)
    axes[0].set_xticks(x_energy[::2], annual_energy.index.to_numpy()[::2])
    axes[0].legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.28), frameon=False, columnspacing=1.0, handlelength=1.2)

    for axis, values, title, denominator in (
        (axes[1], capacity, "(b) Installed power-capacity composition", "Share of installed capacity (%)"),
        (axes[2], generation, "(c) Electricity-generation composition", "Share of electricity generation (%)"),
    ):
        years = values.index.to_numpy()
        x = np.arange(len(years))
        axis.bar(x, values["Thermal"], width=bar_width, color=COLORS["coal"], label="Thermal")
        axis.bar(x, values["Non-thermal"], bottom=values["Thermal"], width=bar_width, color=COLORS["renewable"], label="Non-thermal")
        axis.set_title(title)
        axis.set_ylabel(denominator)
        axis.set_ylim(0, 100)
        axis.set_xticks(x[::2], years[::2])
        axis.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)
    axes[2].set_xlabel("Year")
    for axis in axes:
        axis.grid(axis="y", color="#E6E6E6", linewidth=0.7, zorder=0)
    save(fig, "Figure_5_annual_composition_shares")


def main() -> None:
    style()
    plot_retirement_evidence()
    plot_constraint_typology()
    plot_case_lifecycles()
    plot_annual_composition_shares()
    print(f"Wrote Figures 2--5 to {OUTDIR}")


if __name__ == "__main__":
    main()
