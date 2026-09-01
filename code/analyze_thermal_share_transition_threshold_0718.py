#!/usr/bin/env python3
"""Search for a provincial thermal-generation-share transition threshold.

Thermal generation share is used as an observable proxy for non-clean power.
Transition progress is measured by the forward change in wind-plus-solar
generation share, avoiding the mechanical identity between thermal and
non-thermal generation shares.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_0718.csv"
DATA_DIR = ROOT / "data/thermal_generation_transition_threshold_0718"
TABLE_DIR = ROOT / "result/tables/0718_thermal_threshold"
FIGURE_DIR = ROOT / "result/figures/0718_thermal_threshold"
OUTPUT_DIR = ROOT / "output"

CONTROLS = [
    "ln_gdp",
    "population",
    "sec_pctg",
    "urbanization_rate",
    "env_exp_share",
    "market_index",
]

PROVINCE_CN = {
    "Beijing": "北京",
    "Tianjin": "天津",
    "Hebei": "河北",
    "Shanxi": "山西",
    "Neimenggu": "内蒙古",
    "Liaoning": "辽宁",
    "Jilin": "吉林",
    "Heilongjiang": "黑龙江",
    "Shanghai": "上海",
    "Jiangsu": "江苏",
    "Zhejiang": "浙江",
    "Anhui": "安徽",
    "Fujian": "福建",
    "Jiangxi": "江西",
    "Shandong": "山东",
    "Henan": "河南",
    "Hubei": "湖北",
    "Hunan": "湖南",
    "Guangdong": "广东",
    "Guangxi": "广西",
    "Hainan": "海南",
    "Chongqing": "重庆",
    "Sichuan": "四川",
    "Guizhou": "贵州",
    "Yunnan": "云南",
    "Xizang": "西藏",
    "Shaanxi": "陕西",
    "Gansu": "甘肃",
    "Qinghai": "青海",
    "Ningxia": "宁夏",
    "Xinjiang": "新疆",
}


def normal_two_sided_p(z_value: float) -> float:
    if not np.isfinite(z_value):
        return np.nan
    return math.erfc(abs(z_value) / math.sqrt(2.0))


def regression_design(
    sample: pd.DataFrame,
    threshold: float,
    model: str,
    controls: bool,
) -> tuple[np.ndarray, list[str]]:
    thermal = sample["therm_gen_sh"].to_numpy(dtype=float)
    columns: list[np.ndarray] = [np.ones(len(sample)), thermal]
    names = ["constant", "thermal_share"]

    if model == "jump":
        columns.append((thermal > threshold).astype(float))
        names.append("above_threshold")
    elif model == "kink":
        columns.append(np.maximum(thermal - threshold, 0.0))
        names.append("above_threshold_slope")
    else:
        raise ValueError(f"Unknown threshold model: {model}")

    if controls:
        for variable in CONTROLS:
            values = sample[variable].to_numpy(dtype=float)
            standard_deviation = np.std(values)
            columns.append((values - np.mean(values)) / (standard_deviation or 1.0))
            names.append(variable)

    province_fe = pd.get_dummies(
        sample["province_id"].astype(str), drop_first=True, dtype=float
    ).to_numpy()
    year_fe = pd.get_dummies(
        sample["year"].astype(str), drop_first=True, dtype=float
    ).to_numpy()
    columns.extend([province_fe, year_fe])
    return np.column_stack(columns), names


def clustered_ols(
    design: np.ndarray,
    outcome: np.ndarray,
    clusters: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    coefficients = np.linalg.lstsq(design, outcome, rcond=None)[0]
    residuals = outcome - design @ coefficients
    sse = float(residuals @ residuals)

    inverse_xx = np.linalg.pinv(design.T @ design)
    meat = np.zeros_like(inverse_xx)
    unique_clusters = np.unique(clusters)
    for cluster in unique_clusters:
        index = clusters == cluster
        score = design[index].T @ residuals[index]
        meat += np.outer(score, score)

    observations = len(outcome)
    rank = np.linalg.matrix_rank(design)
    cluster_count = len(unique_clusters)
    correction = 1.0
    if cluster_count > 1 and observations > rank:
        correction = (cluster_count / (cluster_count - 1)) * (
            (observations - 1) / (observations - rank)
        )
    covariance = correction * inverse_xx @ meat @ inverse_xx
    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    return coefficients, standard_errors, sse, residuals


def prepare_forward_changes(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.sort_values(["province_id", "year"]).copy()
    for outcome in ["windsolar_gen_sh", "wind_gen_sh"]:
        for horizon in [1, 2, 3]:
            future_value = panel.groupby("province_id")[outcome].shift(-horizon)
            future_year = panel.groupby("province_id")["year"].shift(-horizon)
            valid_horizon = future_year - panel["year"] == horizon
            panel[f"forward_change_{outcome}_{horizon}y"] = (
                future_value - panel[outcome]
            ).where(valid_horizon)
    return panel


def threshold_search(
    panel: pd.DataFrame,
    outcome: str,
    horizon: int,
    start_year: int,
    controls: bool,
    model: str,
) -> tuple[pd.Series, pd.DataFrame]:
    dependent = f"forward_change_{outcome}_{horizon}y"
    required = ["therm_gen_sh", dependent]
    if controls:
        required.extend(CONTROLS)
    sample = panel.loc[panel["year"] >= start_year].dropna(subset=required).copy()

    lower, upper = sample["therm_gen_sh"].quantile([0.15, 0.85])
    candidates = np.unique(np.round(np.linspace(lower, upper, 141), 4))
    profile_rows: list[dict[str, float | int | str | bool]] = []
    for threshold in candidates:
        below_count = int((sample["therm_gen_sh"] <= threshold).sum())
        above_count = len(sample) - below_count
        if min(below_count, above_count) < 0.15 * len(sample):
            continue

        design, names = regression_design(sample, threshold, model, controls)
        coefficients, standard_errors, sse, _ = clustered_ols(
            design,
            sample[dependent].to_numpy(dtype=float),
            sample["province_id"].to_numpy(),
        )
        term = "above_threshold" if model == "jump" else "above_threshold_slope"
        term_index = names.index(term)
        coefficient = float(coefficients[term_index])
        standard_error = float(standard_errors[term_index])
        z_value = coefficient / standard_error if standard_error > 0 else np.nan
        profile_rows.append(
            {
                "outcome": outcome,
                "horizon_years": horizon,
                "sample_start_year": start_year,
                "controls": controls,
                "model": model,
                "threshold_share": float(threshold),
                "threshold_percent": 100.0 * float(threshold),
                "threshold_term_coefficient": coefficient,
                "clustered_standard_error": standard_error,
                "normal_approximation_p": normal_two_sided_p(z_value),
                "sse": sse,
                "observations": len(sample),
                "provinces": sample["province_id"].nunique(),
                "below_observations": below_count,
                "above_observations": above_count,
            }
        )

    profile = pd.DataFrame(profile_rows).sort_values("threshold_share")
    best = profile.loc[profile["sse"].idxmin()].copy()
    best["sse_improvement_over_worst_percent"] = 100.0 * (
        profile["sse"].max() - best["sse"]
    ) / profile["sse"].max()
    return best, profile


def create_figures(primary_profile: pd.DataFrame, panel: pd.DataFrame) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    best = primary_profile.loc[primary_profile["sse"].idxmin()]
    relative_sse = 100.0 * (
        primary_profile["sse"] / primary_profile["sse"].min() - 1.0
    )
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.plot(primary_profile["threshold_percent"], relative_sse, color="#1f4e79", lw=2)
    ax.axvline(best["threshold_percent"], color="#c00000", ls="--", lw=1.5)
    ax.set_xlabel("Thermal generation share threshold (%)")
    ax.set_ylabel("SSE above the minimum (%)")
    ax.set_title("Three-year wind-solar transition threshold profile")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "Threshold_Profile_3Year_WindSolar.png", dpi=220)
    plt.close(fig)


def leave_one_province_out(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    provinces = panel[["province_id", "province"]].drop_duplicates()
    for province_id, province in provinces.itertuples(index=False):
        best, _ = threshold_search(
            panel.loc[panel["province_id"] != province_id],
            outcome="windsolar_gen_sh",
            horizon=3,
            start_year=2013,
            controls=True,
            model="jump",
        )
        rows.append(
            {
                "excluded_province_id": province_id,
                "excluded_province": province,
                "excluded_province_cn": PROVINCE_CN.get(province, province),
                "threshold_percent": best["threshold_percent"],
                "threshold_term_coefficient": best["threshold_term_coefficient"],
                "normal_approximation_p": best["normal_approximation_p"],
                "observations": best["observations"],
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["threshold_percent", "excluded_province_id"]
    )


def double_threshold_search(
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Search for an acceleration window among thermal-dominant observations."""
    dependent = "forward_change_windsolar_gen_sh_3y"
    required = ["therm_gen_sh", dependent, *CONTROLS]
    sample = panel.loc[
        (panel["year"] >= 2013) & (panel["therm_gen_sh"] >= 0.50)
    ].dropna(subset=required).copy()
    thermal = sample["therm_gen_sh"].to_numpy(dtype=float)
    outcome = sample[dependent].to_numpy(dtype=float)

    common_columns: list[np.ndarray] = [np.ones(len(sample)), thermal]
    for variable in CONTROLS:
        values = sample[variable].to_numpy(dtype=float)
        standard_deviation = np.std(values)
        common_columns.append(
            (values - np.mean(values)) / (standard_deviation or 1.0)
        )
    province_fe = pd.get_dummies(
        sample["province_id"].astype(str), drop_first=True, dtype=float
    ).to_numpy()
    year_fe = pd.get_dummies(
        sample["year"].astype(str), drop_first=True, dtype=float
    ).to_numpy()
    common_design = np.column_stack(common_columns + [province_fe, year_fe])

    lower, upper = np.quantile(thermal, [0.12, 0.88])
    candidates = np.unique(np.round(np.linspace(lower, upper, 81), 4))
    profile_rows: list[dict[str, float | int]] = []
    for first_index, lower_threshold in enumerate(candidates):
        for upper_threshold in candidates[first_index + 1 :]:
            low = thermal <= lower_threshold
            middle = (thermal > lower_threshold) & (thermal <= upper_threshold)
            high = thermal > upper_threshold
            if min(low.sum(), middle.sum(), high.sum()) < 0.10 * len(sample):
                continue
            design = np.column_stack(
                [common_design, middle.astype(float), high.astype(float)]
            )
            coefficients, standard_errors, sse, _ = clustered_ols(
                design,
                outcome,
                sample["province_id"].to_numpy(),
            )
            profile_rows.append(
                {
                    "lower_threshold_percent": 100.0 * lower_threshold,
                    "upper_threshold_percent": 100.0 * upper_threshold,
                    "middle_vs_low_coefficient": coefficients[-2],
                    "middle_vs_low_standard_error": standard_errors[-2],
                    "middle_vs_low_p": normal_two_sided_p(
                        coefficients[-2] / standard_errors[-2]
                    ),
                    "high_vs_low_coefficient": coefficients[-1],
                    "high_vs_low_standard_error": standard_errors[-1],
                    "high_vs_low_p": normal_two_sided_p(
                        coefficients[-1] / standard_errors[-1]
                    ),
                    "sse": sse,
                    "low_observations": int(low.sum()),
                    "middle_observations": int(middle.sum()),
                    "high_observations": int(high.sum()),
                }
            )

    profile = pd.DataFrame(profile_rows).sort_values("sse").reset_index(drop=True)
    best = profile.iloc[0].copy()
    lower_threshold = best["lower_threshold_percent"] / 100.0
    upper_threshold = best["upper_threshold_percent"] / 100.0
    low = thermal <= lower_threshold
    high = thermal > upper_threshold

    # Rebase on the middle regime to test the loss of momentum above the upper break.
    rebased_design = np.column_stack(
        [common_design, low.astype(float), high.astype(float)]
    )
    coefficients, standard_errors, _, _ = clustered_ols(
        rebased_design,
        outcome,
        sample["province_id"].to_numpy(),
    )
    best["low_vs_middle_coefficient"] = coefficients[-2]
    best["low_vs_middle_standard_error"] = standard_errors[-2]
    best["low_vs_middle_p"] = normal_two_sided_p(
        coefficients[-2] / standard_errors[-2]
    )
    best["high_vs_middle_coefficient"] = coefficients[-1]
    best["high_vs_middle_standard_error"] = standard_errors[-1]
    best["high_vs_middle_p"] = normal_two_sided_p(
        coefficients[-1] / standard_errors[-1]
    )
    best["observations"] = len(sample)
    best["provinces"] = sample["province_id"].nunique()
    best["sample_definition"] = "year>=2013 and thermal generation share>=50%"
    return pd.DataFrame([best]), profile


def fast_double_threshold_fit(sample: pd.DataFrame) -> dict[str, float]:
    """Fit the double threshold after partialling out controls and fixed effects."""
    dependent = "forward_change_windsolar_gen_sh_3y"
    thermal = sample["therm_gen_sh"].to_numpy(dtype=float)
    outcome = sample[dependent].to_numpy(dtype=float)

    common_columns: list[np.ndarray] = [np.ones(len(sample)), thermal]
    for variable in CONTROLS:
        values = sample[variable].to_numpy(dtype=float)
        standard_deviation = np.std(values)
        common_columns.append(
            (values - np.mean(values)) / (standard_deviation or 1.0)
        )
    province_fe = pd.get_dummies(
        sample["bootstrap_province_id"].astype(str), drop_first=True, dtype=float
    ).to_numpy()
    year_fe = pd.get_dummies(
        sample["year"].astype(str), drop_first=True, dtype=float
    ).to_numpy()
    common_design = np.column_stack(common_columns + [province_fe, year_fe])

    lower, upper = np.quantile(thermal, [0.12, 0.88])
    candidates = np.unique(np.round(np.linspace(lower, upper, 61), 4))
    step_indicators = np.column_stack(
        [(thermal > candidate).astype(float) for candidate in candidates]
    )
    stacked_outcomes = np.column_stack([outcome, step_indicators])
    common_coefficients = np.linalg.lstsq(
        common_design, stacked_outcomes, rcond=None
    )[0]
    residualized = stacked_outcomes - common_design @ common_coefficients
    residualized_outcome = residualized[:, 0]
    residualized_steps = residualized[:, 1:]

    best: tuple[float, float, float, float, float] | None = None
    minimum_regime_size = 0.10 * len(sample)
    for lower_index, lower_threshold in enumerate(candidates[:-1]):
        for upper_index in range(lower_index + 1, len(candidates)):
            upper_threshold = candidates[upper_index]
            low_count = int((thermal <= lower_threshold).sum())
            middle_count = int(
                ((thermal > lower_threshold) & (thermal <= upper_threshold)).sum()
            )
            high_count = len(sample) - low_count - middle_count
            if min(low_count, middle_count, high_count) < minimum_regime_size:
                continue

            residualized_middle = (
                residualized_steps[:, lower_index]
                - residualized_steps[:, upper_index]
            )
            residualized_high = residualized_steps[:, upper_index]
            threshold_design = np.column_stack(
                [residualized_middle, residualized_high]
            )
            coefficients = np.linalg.lstsq(
                threshold_design, residualized_outcome, rcond=None
            )[0]
            residuals = residualized_outcome - threshold_design @ coefficients
            sse = float(residuals @ residuals)
            candidate_result = (
                sse,
                float(lower_threshold),
                float(upper_threshold),
                float(coefficients[0]),
                float(coefficients[1] - coefficients[0]),
            )
            if best is None or candidate_result[0] < best[0]:
                best = candidate_result

    if best is None:
        raise RuntimeError("No admissible double-threshold bootstrap model")
    return {
        "lower_threshold_percent": 100.0 * best[1],
        "upper_threshold_percent": 100.0 * best[2],
        "middle_vs_low_coefficient": best[3],
        "high_vs_middle_coefficient": best[4],
    }


def bootstrap_double_threshold(
    panel: pd.DataFrame,
    repetitions: int = 500,
    seed: int = 20260718,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dependent = "forward_change_windsolar_gen_sh_3y"
    required = ["therm_gen_sh", dependent, *CONTROLS]
    sample = panel.loc[
        (panel["year"] >= 2013) & (panel["therm_gen_sh"] >= 0.50)
    ].dropna(subset=required).copy()
    province_ids = sample["province_id"].unique()
    random = np.random.default_rng(seed)

    rows: list[dict[str, float | int]] = []
    for repetition in range(1, repetitions + 1):
        pieces: list[pd.DataFrame] = []
        sampled_provinces = random.choice(
            province_ids, size=len(province_ids), replace=True
        )
        for bootstrap_id, province_id in enumerate(sampled_provinces):
            piece = sample.loc[sample["province_id"] == province_id].copy()
            piece["bootstrap_province_id"] = bootstrap_id
            pieces.append(piece)
        bootstrap_sample = pd.concat(pieces, ignore_index=True)
        result = fast_double_threshold_fit(bootstrap_sample)
        result["bootstrap_repetition"] = repetition
        rows.append(result)

    draws = pd.DataFrame(rows)
    confidence_rows: list[dict[str, float | str | int]] = []
    for variable in [
        "lower_threshold_percent",
        "upper_threshold_percent",
        "middle_vs_low_coefficient",
        "high_vs_middle_coefficient",
    ]:
        confidence_rows.append(
            {
                "variable": variable,
                "bootstrap_repetitions": repetitions,
                "percentile_2_5": draws[variable].quantile(0.025),
                "bootstrap_median": draws[variable].median(),
                "percentile_97_5": draws[variable].quantile(0.975),
            }
        )
    return draws, pd.DataFrame(confidence_rows)


def create_binned_transition_table(panel: pd.DataFrame) -> pd.DataFrame:
    dependent = "forward_change_windsolar_gen_sh_3y"
    sample = panel.loc[panel["year"] >= 2013].dropna(
        subset=["therm_gen_sh", dependent]
    ).copy()
    sample["thermal_share_bin"] = pd.qcut(
        sample["therm_gen_sh"], q=10, duplicates="drop"
    )
    binned = (
        sample.groupby("thermal_share_bin", observed=True)
        .agg(
            thermal_share=("therm_gen_sh", "mean"),
            transition=(dependent, "mean"),
            observations=(dependent, "size"),
        )
        .reset_index(drop=True)
    )
    binned.to_csv(TABLE_DIR / "Table_0718_ThermalShare_BinnedTransition.csv", index=False)
    return binned


def write_interpretation(
    results: pd.DataFrame,
    latest: pd.DataFrame,
    leave_one_out: pd.DataFrame,
    primary_profile: pd.DataFrame,
    double_threshold: pd.DataFrame,
    bootstrap_confidence: pd.DataFrame,
) -> None:
    primary = results.loc[
        (results["outcome"] == "windsolar_gen_sh")
        & (results["horizon_years"] == 3)
        & (results["sample_start_year"] == 2013)
        & results["controls"]
        & (results["model"] == "jump")
    ].iloc[0]
    controlled_jump = results.loc[
        (results["outcome"] == "windsolar_gen_sh")
        & results["controls"]
        & (results["model"] == "jump")
    ]
    thresholds = controlled_jump["threshold_percent"]
    positive = int((controlled_jump["threshold_term_coefficient"] > 0).sum())
    negative = int((controlled_jump["threshold_term_coefficient"] < 0).sum())
    competing = primary_profile.loc[
        primary_profile["threshold_percent"].between(88.0, 93.0)
    ].nsmallest(1, "sse").iloc[0]
    double = double_threshold.iloc[0]
    bootstrap_ci = bootstrap_confidence.set_index("variable")
    lower_ci = bootstrap_ci.loc["lower_threshold_percent"]
    upper_ci = bootstrap_ci.loc["upper_threshold_percent"]
    middle_ci = bootstrap_ci.loc["middle_vs_low_coefficient"]
    high_ci = bootstrap_ci.loc["high_vs_middle_coefficient"]

    text = f"""# 省级火电发电占比与新能源转型跃迁点检验

## 指标和模型

- 非清洁能源发电比例：使用火电发电量占总发电量的比例作为代理。火电包含煤电、气电和油电，因此不能严格等同于煤电比例。
- 转型推进：使用未来一年、两年和三年的风光发电占比增量。没有使用非火电占比增量，避免与火电占比形成机械的加总关系。
- 阈值模型：在省份固定效应和年份固定效应基础上，控制地区生产总值、人口、第二产业占比、城镇化、环保财政支出占比和市场化指数；在火电占比的第15至第85百分位之间搜索使残差平方和最小的断点。

## 主要结果

以2013年以后样本、三年期风光发电占比增量和完整控制变量为主设定，残差平方和最低的候选断点为 **{primary['threshold_percent']:.2f}%**。在该设定中，火电占比高于断点的观测，其未来三年风光发电占比增量高出 **{100.0 * primary['threshold_term_coefficient']:.2f} 个百分点**，未经阈值搜索校正的正态近似 p 值为 **{primary['normal_approximation_p']:.4f}**。这一结果可以被解释为高火电占比地区在中期窗口中存在更强的转型压力或追赶动力，但不能作为严格的阈值显著性检验。

但是，该断点不是稳定的全国统一跃迁点。主设定的残差函数还存在约 **{competing['threshold_percent']:.2f}%** 的竞争断点，而且该断点对应的系数为 **{100.0 * competing['threshold_term_coefficient']:.2f} 个百分点**，方向与78%断点相反。受预测期限、样本起始年份和模型形式影响，带控制变量的跳跃模型候选断点分布在 **{thresholds.min():.2f}%—{thresholds.max():.2f}%**；阈值项共有 {positive} 个正系数和 {negative} 个负系数，方向并不一致。逐省剔除检验的断点中位数为 **{leave_one_out['threshold_percent'].median():.2f}%**，但第25百分位和第75百分位分别为 **{leave_one_out['threshold_percent'].quantile(.25):.2f}%** 和 **{leave_one_out['threshold_percent'].quantile(.75):.2f}%**，同样显示约78%与约91%两个断点簇。

## 可以报告的判断

当前数据只能给出一个探索性判断：**约78%的火电发电占比是主设定下的候选压力阈值，但尚不能认定为各省共同的转型跃迁点。** 更稳妥的结论是，新能源转型速度对既有火电结构存在非线性，而且这种非线性具有明显的省际异质性。

进一步将样本限定为火电占比不低于50%的火电主导观测，并允许存在两个断点，模型得到 **{double['lower_threshold_percent']:.2f}%** 和 **{double['upper_threshold_percent']:.2f}%** 两个候选界点。处于两者之间的观测，未来三年风光发电占比增量比低于下界的观测高 **{100.0 * double['middle_vs_low_coefficient']:.2f} 个百分点**，未经阈值搜索校正的 p 值为 **{double['middle_vs_low_p']:.4f}**；高于上界后，风光增长动能相对中间区间下降 **{abs(100.0 * double['high_vs_middle_coefficient']):.2f} 个百分点**，p 值为 **{double['high_vs_middle_p']:.4f}**。因此，更有信息量的描述是：约78%附近可能出现转型压力启动，而约92%以上可能进入深度火电锁定区间。

按省份整体重抽样500次并在每个自助样本中重新搜索断点后，下界的百分位法95%区间为 **[{lower_ci['percentile_2_5']:.2f}%, {lower_ci['percentile_97_5']:.2f}%]**，上界为 **[{upper_ci['percentile_2_5']:.2f}%, {upper_ci['percentile_97_5']:.2f}%]**。中间区间相对低区间的增量效应95%区间为 **[{100.0 * middle_ci['percentile_2_5']:.2f}, {100.0 * middle_ci['percentile_97_5']:.2f}] 个百分点**；高区间相对中间区间的效应区间为 **[{100.0 * high_ci['percentile_2_5']:.2f}, {100.0 * high_ci['percentile_97_5']:.2f}] 个百分点**。两个效应区间均包含零，说明断点位置和区间效应仍有较大抽样不确定性。

截至2023年，共有 {int((latest['therm_gen_sh'] > primary['threshold_share']).sum())} 个省级行政单位的火电发电占比高于主设定候选阈值。该分组只适合描述，不应直接解释为因果处理组。

## 下一步识别

若要把“跃迁点”写进论文，需要补充煤电而非火电发电比例，并将省份按风光型、水电型、核电型和纯火电型分组估计；同时应使用更长的风光发电序列，并进一步构造适用于非标准阈值估计的似然比置信集合。当前结果更适合作为非线性事实和后续假说，而不是新的主识别结论。
"""
    (OUTPUT_DIR / "0718_火电发电占比转型跃迁点检验.md").write_text(
        text, encoding="utf-8"
    )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    panel = pd.read_csv(INPUT)
    panel = prepare_forward_changes(panel)
    panel["province_cn"] = panel["province"].map(PROVINCE_CN).fillna(panel["province"])

    province_panel_columns = [
        "province_id",
        "province",
        "province_cn",
        "year",
        "total_generation_billion_kwh",
        "thermal_generation_billion_kwh",
        "therm_gen_sh",
        "nontherm_gen_sh",
        "wind_gen_sh",
        "solar_gen_sh",
        "windsolar_gen_sh",
    ]
    province_panel = panel[province_panel_columns].copy()
    province_panel.to_csv(
        DATA_DIR / "province_thermal_generation_share_2000_2023.csv", index=False
    )

    latest = (
        province_panel.loc[province_panel["year"] == 2023]
        .sort_values("therm_gen_sh", ascending=False)
        .reset_index(drop=True)
    )
    latest["thermal_generation_share_percent"] = 100.0 * latest["therm_gen_sh"]
    latest["windsolar_generation_share_percent"] = 100.0 * latest["windsolar_gen_sh"]
    latest.to_csv(DATA_DIR / "province_thermal_generation_share_2023.csv", index=False)

    specifications: list[dict[str, object]] = []
    primary_profile: pd.DataFrame | None = None
    for outcome in ["windsolar_gen_sh", "wind_gen_sh"]:
        for horizon in [1, 2, 3]:
            for start_year in [2013, 2014, 2015, 2016]:
                for controls in [False, True]:
                    for model in ["jump", "kink"]:
                        best, profile = threshold_search(
                            panel,
                            outcome,
                            horizon,
                            start_year,
                            controls,
                            model,
                        )
                        specifications.append(best.to_dict())
                        if (
                            outcome == "windsolar_gen_sh"
                            and horizon == 3
                            and start_year == 2013
                            and controls
                            and model == "jump"
                        ):
                            primary_profile = profile

    results = pd.DataFrame(specifications).sort_values(
        ["outcome", "model", "controls", "sample_start_year", "horizon_years"]
    )
    results.to_csv(TABLE_DIR / "Table_0718_ThermalShare_ThresholdSearch.csv", index=False)
    latest.to_csv(TABLE_DIR / "Table_0718_ThermalShare_Province2023.csv", index=False)
    leave_one_out = leave_one_province_out(panel)
    leave_one_out.to_csv(
        TABLE_DIR / "Table_0718_ThermalShare_LeaveOneProvinceOut.csv", index=False
    )
    binned = create_binned_transition_table(panel)
    double_threshold, double_profile = double_threshold_search(panel)
    double_threshold.to_csv(
        TABLE_DIR / "Table_0718_ThermalShare_DoubleThreshold.csv", index=False
    )
    double_profile.to_csv(
        TABLE_DIR / "Table_0718_ThermalShare_DoubleThresholdProfile.csv", index=False
    )
    bootstrap_draws, bootstrap_confidence = bootstrap_double_threshold(panel)
    bootstrap_draws.to_csv(
        TABLE_DIR / "Table_0718_ThermalShare_DoubleThresholdBootstrapDraws.csv",
        index=False,
    )
    bootstrap_confidence.to_csv(
        TABLE_DIR / "Table_0718_ThermalShare_DoubleThresholdBootstrapCI.csv",
        index=False,
    )

    with pd.ExcelWriter(
        TABLE_DIR / "ThermalShare_TransitionThreshold_0718.xlsx", engine="openpyxl"
    ) as writer:
        latest.to_excel(writer, sheet_name="2023省级火电占比", index=False)
        results.to_excel(writer, sheet_name="阈值稳定性检验", index=False)
        leave_one_out.to_excel(writer, sheet_name="逐省剔除检验", index=False)
        double_threshold.to_excel(writer, sheet_name="双阈值主结果", index=False)
        bootstrap_confidence.to_excel(writer, sheet_name="双阈值Bootstrap区间", index=False)
        binned.to_excel(writer, sheet_name="十分位描述", index=False)
        province_panel.to_excel(writer, sheet_name="省级年度面板", index=False)

    if primary_profile is not None:
        primary_profile.to_csv(
            TABLE_DIR / "Table_0718_ThermalShare_PrimaryProfile.csv", index=False
        )
        create_figures(primary_profile, panel)
        write_interpretation(
            results,
            latest,
            leave_one_out,
            primary_profile,
            double_threshold,
            bootstrap_confidence,
        )

    print(f"Input rows: {len(panel)}")
    print(f"2023 provinces: {len(latest)}")
    print(f"Threshold specifications: {len(results)}")
    print(f"Tables: {TABLE_DIR}")
    print(f"Interpretation: {OUTPUT_DIR / '0718_火电发电占比转型跃迁点检验.md'}")


if __name__ == "__main__":
    main()
