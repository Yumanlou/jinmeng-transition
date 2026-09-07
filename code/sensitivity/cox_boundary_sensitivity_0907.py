#!/usr/bin/env python3
"""Cox sensitivity analysis for retirement events at calendar-period boundaries.

This script leaves the 0820 analysis and its outputs untouched.  It reproduces
the saved continuous-exposure specification and changes only how an annual
retirement year is mapped to continuous analysis time:

* original_start_of_year: event time is retired_year (the 0820 convention);
* end_of_reported_year: event time is retired_year + 1 (primary sensitivity);
* middle_of_reported_year: event time is retired_year + 0.5 (auxiliary check).

Events are assigned to policy periods by their reported retirement year, not by
the shifted continuous event time.  Calendar periods are otherwise the same as
in the 0820 script, and left truncation is retained.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import lifelines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter


ROOT = Path(__file__).resolve().parents[2]
GEM = ROOT / "data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv"
MAIN = ROOT / (
    "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_"
    "cleanproxy_tide_absorption_monthly_reliability_policyworkreports_"
    "projectlifecycle_leadership_0721.csv"
)
SAVED_0820 = ROOT / "result/tables/0820_coal_retirement_survival_final/period_specific_cox.csv"
TABLE_DIR = ROOT / "result/tables/0907_cox_boundary_sensitivity"
FIGURE_DIR = ROOT / "result/figures/0907_cox_boundary_sensitivity"

EXCLUDE = {
    "cancelled", "construction", "announced", "shelved", "permitted",
    "pre-permit", "mothballed",
}
PERIODS = [
    ("pre_2000_2011", 2000, 2011),
    ("early_2012_2015", 2012, 2015),
    ("supply_2016_2020", 2016, 2020),
    ("carbon_2021_2025", 2021, 2025),
]
TIMING_OFFSETS = {
    "original_start_of_year": 0.0,
    "end_of_reported_year": 1.0,
    "middle_of_reported_year": 0.5,
}
PRIMARY_COMPARISON = {"original_start_of_year", "end_of_reported_year"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_exposure() -> dict[str, float]:
    exposure: dict[str, float] = {}
    with MAIN.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                exposure[row["province"]] = float(row["coalexp_pre"])
            except (KeyError, TypeError, ValueError):
                continue
    return exposure


def load_eligible_units(exposure: dict[str, float]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    with GEM.open(encoding="utf-8-sig", newline="") as handle:
        for unit_id, row in enumerate(csv.DictReader(handle)):
            if row.get("asset") != "coal" or row.get("status") in EXCLUDE:
                continue
            try:
                start_year = float(row["start_year"])
                capacity = float(row["capacity_mw"])
            except (KeyError, TypeError, ValueError):
                continue
            province = row.get("province")
            if province not in exposure:
                continue
            try:
                retired_year = (
                    float(row["retired_year"]) if row.get("retired_year") else np.nan
                )
            except ValueError:
                continue
            if not math.isnan(retired_year) and retired_year < start_year:
                continue
            rows.append(
                {
                    "unit_id": unit_id,
                    "gem_id": row.get("gem_id", ""),
                    "province": province,
                    "start_year": start_year,
                    "retired_year": retired_year,
                    "capacity_mw": capacity,
                    "coalexp": exposure[province],
                }
            )
    return pd.DataFrame(rows)


def build_episodes(units: pd.DataFrame, timing: str) -> pd.DataFrame:
    offset = TIMING_OFFSETS[timing]
    rows: list[dict[str, object]] = []
    for unit in units.itertuples(index=False):
        retired = None if pd.isna(unit.retired_year) else float(unit.retired_year)
        event_time = None if retired is None else retired + offset
        for period, first_year, last_year in PERIODS:
            if unit.start_year > last_year or (retired is not None and retired < first_year):
                continue
            interval_start = max(float(unit.start_year), float(first_year))
            interval_end = min(
                event_time if event_time is not None else float(last_year + 1),
                float(last_year + 1),
            )
            if interval_end <= interval_start:
                continue
            event = int(retired is not None and first_year <= retired <= last_year)
            rows.append(
                {
                    "unit_id": unit.unit_id,
                    "province": unit.province,
                    "period": period,
                    "entry_age": interval_start - unit.start_year,
                    "exit_age": interval_end - unit.start_year,
                    "event": event,
                    "coalexp": unit.coalexp,
                    "capacity_100mw": unit.capacity_mw / 100.0,
                    "vintage_decade": (unit.start_year - 2000.0) / 10.0,
                }
            )
    return pd.DataFrame(rows)


def make_design(episodes: pd.DataFrame, exposure: dict[str, float]) -> pd.DataFrame:
    df = episodes.copy()
    province_exposure = pd.Series(list(exposure.values()), dtype=float)
    df["exposure"] = (
        (df["coalexp"] - province_exposure.mean()) / province_exposure.std(ddof=1)
    )
    for period, _, _ in PERIODS:
        df[f"exposure_{period}"] = (
            df["exposure"] * df["period"].eq(period).astype(float)
        )
    for period, _, _ in PERIODS[1:]:
        df[f"period_{period}"] = df["period"].eq(period).astype(float)
    return df


def fit_specification(
    units: pd.DataFrame, exposure: dict[str, float], timing: str
) -> tuple[list[dict[str, object]], pd.DataFrame]:
    episodes = build_episodes(units, timing)
    df = make_design(episodes, exposure)
    exposure_terms = [f"exposure_{period}" for period, _, _ in PERIODS]
    period_terms = [f"period_{period}" for period, _, _ in PERIODS[1:]]
    formula = " + ".join(
        exposure_terms + period_terms + ["capacity_100mw", "vintage_decade"]
    )
    model = CoxPHFitter()
    model.fit(
        df,
        duration_col="exit_age",
        event_col="event",
        entry_col="entry_age",
        cluster_col="province",
        robust=True,
        formula=formula,
    )

    results: list[dict[str, object]] = []
    for period, _, _ in PERIODS:
        term = f"exposure_{period}"
        summary = model.summary.loc[term]
        period_df = df.loc[df["period"].eq(period)]
        se = float(summary["se(coef)"])
        coef = float(summary["coef"])
        results.append(
            {
                "specification": timing,
                "period": period,
                "units": int(df["unit_id"].nunique()),
                "retirement_events": int(df["event"].sum()),
                "risk_intervals": int(len(df)),
                "period_units": int(period_df["unit_id"].nunique()),
                "period_retirement_events": int(period_df["event"].sum()),
                "period_risk_intervals": int(len(period_df)),
                "coef": coef,
                "hazard_ratio": float(math.exp(coef)),
                "clustered_se_coef": se,
                "p_value": float(summary["p"]),
                "ci95_lower_hr": float(math.exp(coef - 1.959963984540054 * se)),
                "ci95_upper_hr": float(math.exp(coef + 1.959963984540054 * se)),
            }
        )
    return results, episodes


def boundary_event_audit(units: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for boundary in (2000, 2012, 2016, 2021):
        at_boundary = units.loc[units["retired_year"].eq(float(boundary))]
        rows.append(
            {
                "boundary_year": boundary,
                "eligible_retirement_events": int(len(at_boundary)),
                "original_positive_duration_events": 0,
                "original_zero_duration_excluded_events": int(len(at_boundary)),
                "events_added_by_end_of_year_encoding": int(len(at_boundary)),
            }
        )
    return pd.DataFrame(rows)


def validate_original_reproduction(results: pd.DataFrame) -> None:
    saved = pd.read_csv(SAVED_0820, encoding="utf-8-sig")
    saved = saved.loc[saved["specification"].eq("standardized_continuous")].copy()
    reproduced = results.loc[
        results["specification"].eq("original_start_of_year")
    ].copy()
    merged = saved.merge(reproduced, on="period", validate="one_to_one")
    if set(merged["risk_intervals"]) != {12344}:
        raise AssertionError("Original risk-interval count was not reproduced")
    if set(merged["retirement_events"]) != {952}:
        raise AssertionError("Original event count was not reproduced")
    for saved_col, new_col in [
        ("hazard_ratio_x", "hazard_ratio_y"),
        ("se_cluster_province", "clustered_se_coef"),
        ("p", "p_value"),
    ]:
        if not np.allclose(merged[saved_col], merged[new_col], rtol=1e-7, atol=1e-9):
            raise AssertionError(f"Original estimates differ for {saved_col}")


def make_figure(results: pd.DataFrame) -> None:
    labels = [
        "2000–2011", "2012–2015", "2016–2020", "2021–2025"
    ]
    specs = [
        ("original_start_of_year", "Original (0820)", "#6B7280", "o"),
        ("end_of_reported_year", "End-of-reported-year", "#0072B2", "s"),
        ("middle_of_reported_year", "Mid-reported-year", "#D55E00", "^"),
    ]
    offsets = [-0.18, 0.0, 0.18]
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for (spec, label, color, marker), offset in zip(specs, offsets):
        subset = results.loc[results["specification"].eq(spec)].set_index("period")
        subset = subset.loc[[p[0] for p in PERIODS]]
        y = np.arange(4, dtype=float) + offset
        hr = subset["hazard_ratio"].to_numpy()
        lower = subset["ci95_lower_hr"].to_numpy()
        upper = subset["ci95_upper_hr"].to_numpy()
        ax.errorbar(
            hr, y, xerr=np.vstack([hr - lower, upper - hr]), fmt=marker,
            color=color, capsize=3, linewidth=1.4, markersize=5.5, label=label,
        )
    ax.axvline(1.0, color="black", linewidth=0.9, linestyle="--")
    ax.set_yticks(np.arange(4), labels)
    ax.invert_yaxis()
    ax.set_xlabel("Hazard ratio per 1-SD higher pre-policy coal exposure")
    ax.set_title("Cox timing sensitivity for annual retirement years")
    ax.grid(axis="x", color="#D1D5DB", linewidth=0.6)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "cox_boundary_hr_comparison.png", dpi=240)
    fig.savefig(FIGURE_DIR / "cox_boundary_hr_comparison.pdf")
    plt.close(fig)


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    exposure = load_exposure()
    units = load_eligible_units(exposure)

    all_results: list[dict[str, object]] = []
    episode_counts: dict[str, dict[str, int]] = {}
    for timing in TIMING_OFFSETS:
        results, episodes = fit_specification(units, exposure, timing)
        all_results.extend(results)
        episode_counts[timing] = {
            "units": int(episodes["unit_id"].nunique()),
            "events": int(episodes["event"].sum()),
            "intervals": int(len(episodes)),
        }

    results_df = pd.DataFrame(all_results)
    validate_original_reproduction(results_df)
    boundary_df = boundary_event_audit(units)
    if int(boundary_df["original_zero_duration_excluded_events"].sum()) != 126:
        raise AssertionError("Expected 126 excluded boundary events")
    inclusive = episode_counts["end_of_reported_year"]
    if inclusive != {"units": 4326, "events": 1078, "intervals": 12470}:
        raise AssertionError(f"Unexpected inclusive episode counts: {inclusive}")

    results_df.to_csv(
        TABLE_DIR / "cox_boundary_model_results.csv", index=False, encoding="utf-8-sig"
    )
    results_df.loc[results_df["specification"].isin(PRIMARY_COMPARISON)].to_csv(
        TABLE_DIR / "cox_boundary_primary_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )
    boundary_df.to_csv(
        TABLE_DIR / "boundary_event_audit.csv", index=False, encoding="utf-8-sig"
    )
    make_figure(results_df)

    metadata = {
        "script": str(Path(__file__).relative_to(ROOT)),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            "lifelines": lifelines.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "matplotlib": plt.matplotlib.__version__,
        },
        "inputs": {
            str(GEM.relative_to(ROOT)): sha256(GEM),
            str(MAIN.relative_to(ROOT)): sha256(MAIN),
            str(SAVED_0820.relative_to(ROOT)): sha256(SAVED_0820),
        },
        "eligible_units": int(len(units)),
        "province_exposure_count": int(len(exposure)),
        "timing_offsets": TIMING_OFFSETS,
        "episode_counts": episode_counts,
        "formula": (
            "exposure_pre_2000_2011 + exposure_early_2012_2015 + "
            "exposure_supply_2016_2020 + exposure_carbon_2021_2025 + "
            "period_early_2012_2015 + period_supply_2016_2020 + "
            "period_carbon_2021_2025 + capacity_100mw + vintage_decade"
        ),
        "cluster": "province",
        "robust": True,
        "entry_col": "entry_age",
        "validation": {
            "original_saved_estimates_reproduced": True,
            "excluded_boundary_events_total": 126,
            "inclusive_expected_counts_reproduced": True,
        },
    }
    (TABLE_DIR / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
