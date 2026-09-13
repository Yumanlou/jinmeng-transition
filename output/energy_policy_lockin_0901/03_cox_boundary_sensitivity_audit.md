# Cox survival 阶段边界事件：方法诊断与敏感性检验

审计日期：2026-09-07  
审计范围：仅检查 annual retirement-year 的连续时间映射及其阶段边界后果；不改变 Cox 估计器、样本筛选、暴露变量、控制变量、聚类或左截断设定。  
运行环境：Python 3.13.2；`lifelines 0.30.0`；pandas 3.0.5；NumPy 2.2.6；Matplotlib 3.10.3。

## 结论摘要

当前 0820 规格将 `retired_year` 直接当作连续事件时点。对任何在阶段首年退役的机组，阶段内的 `interval_start` 与 `interval_end` 都等于该首年，因而形成零时长区间并被删除。126 个事件的排除可由这条机械规则完全解释；原脚本和较早脚本没有给出将阶段首年事件系统排除在风险集外的方法论理由。因此，这更符合**时间编码副作用**，而不是有文档支持的方法设计。

主敏感性把退役年解释为该报告年度结束时发生，即事件时点设为 `retired_year + 1`，同时仍按原始 `retired_year` 把事件归入四个日历阶段。这一规则对所有年份一致、不依赖阶段切点，并保留全部 126 个边界事件。其余模型要素与 0820 完全相同，且仍由 `lifelines.CoxPHFitter` 估计。

边界纳入后，样本由 4,323 台正时长风险机组、952 个 modeled events、12,344 个 unit-period intervals 变为 4,326 台、1,078 个事件、12,470 个区间。四期 HR 的方向均未改变，仍全部大于 1；相对变化为 +2.9%、+10.2%、+4.0% 和 −1.2%。三个 post-2012 HR 仍均不显著，95% CI 均跨 1。因此，结果不支持“post-2012 存在可统计识别的、随基期煤炭暴露增强的退役加速”。但若“acceleration”指 post 与 pre 系数之间的正式差异，则仍需省级聚类稳健的跨期线性检验；仅凭各期相对 1 的 p 值不能把“无差异”作为正式检验结论。

基于数据完整性而非显著性，建议把边界事件纳入规格作为主 Cox 表和 Figure 2 的基础，把 952-event 版本明确降为 legacy/robustness specification。

---

## A. 事实

### A1. 审查材料与软件实现

本阶段只读检查了：

- `code/coal_retirement_survival_final_0820.py`；
- `code/coal_retirement_survival.py`；
- `code/coal_retirement_survival_segmented.py`；
- `code/plot_energy_policy_evidence_figures_0822.py`；
- `output/energy_policy_lockin_0901/02_high_priority_evidence_diagnosis.md`；
- `result/tables/0820_coal_retirement_survival_final/period_specific_cox.csv`；
- 较早 survival 结果及本阶段新生成的敏感性结果。

运行前确认：

- `import lifelines` 成功，版本为 **0.30.0**；
- 敏感性脚本导入并实例化 `lifelines.CoxPHFitter`；
- 被否决的自写 partial likelihood、gradient、Hessian 或 sandwich estimator 补丁没有生效；
- 敏感性脚本成功逐项复现 0820 continuous-exposure 规格的四期 HR、clustered SE、p 值以及 4,323/952/12,344 计数。

### A2. annual-time 数据的实际含义

当前模型输入中，与寿命有关的字段是 `start_year` 和 `retired_year`。GEM 构建脚本从源工作簿的 `Start year`、`Retired year` 两列读取并数值化；进入 Cox 的派生 CSV 没有投产或退役的月、日字段。因此：

- 数据能识别报告年份，不能识别年内的精确事件顺序；
- `start_year = Y`、`retired_year = R` 本身不等于“1 月 1 日投产/退役”；
- 把年度整数直接放入连续时间 Cox，必须附加一个明确的年内时点约定。

### A3. 0820 规格如何构造风险区间

对阶段 `[first_year, last_year]`，当前最终脚本实际使用：

```text
interval_start = max(start_year, first_year)
interval_end   = min(retired_year, last_year + 1)  # 若未退役则 last_year + 1
entry_age      = interval_start - start_year
exit_age       = interval_end - start_year
event          = 1{first_year <= retired_year <= last_year}
删除 interval_end <= interval_start 的记录
```

因此，若 `retired_year == first_year`：

```text
interval_start = first_year
interval_end   = first_year
```

该事件形成零时长 interval，随后被删除；它又不属于上一阶段，所以不会在其他阶段进入模型。这个结论与机组是否在边界年投产无关。

### A4. 被排除的边界事件

| 阶段首年 | 合格退役事件 | 0820 中进入模型 | 主敏感性新增 |
|---:|---:|---:|---:|
| 2000 | 3 | 0 | 3 |
| 2012 | 30 | 0 | 30 |
| 2016 | 74 | 0 | 74 |
| 2021 | 19 | 0 | 19 |
| **合计** | **126** | **0** | **126** |

三台仅在 2000 年产生零时长记录、因而完全不进入 0820 风险区间的机组，在边界纳入规格中也得到保留。这解释了 unique contributing units 从 4,323 增至 4,326。

### A5. 这是否是明确的方法设计

不是。最终脚本说明了日历阶段、左截断、标准化连续暴露、控制变量和省级聚类，但没有说明或论证“阶段首年退役不进入模型”。两个较早 survival 脚本也通过 `dur <= entry` 的机械条件产生同类排除，没有单独的方法声明。因此，现有证据支持将其判断为**连续时间映射与阶段切分共同产生的编码副作用**。

### A6. 保持不变的主规格

敏感性估计除时间/区间编码外保持：

- 相同 eligible-unit rules 与 `EXCLUDE` 状态集合；
- 相同四个日历阶段：2000–2011、2012–2015、2016–2020、2021–2025；
- 相同 30 省 `coalexp_pre`、按省级暴露分布样本标准差标准化；
- 相同 `capacity_100mw` 与 `vintage_decade` 控制；
- 相同阶段虚拟变量与 exposure × period 项；
- 相同 `CoxPHFitter`、左截断 `entry_col=entry_age`；
- 相同 `cluster_col=province, robust=True`；
- 相同 `lifelines` ties handling。

---

## B. 方法判断

### B1. 推荐的 boundary-inclusive annual-time 编码

主敏感性采用**报告年度年末约定**：

```text
commissioning entry time = start_year
retirement event time    = retired_year + 1
period endpoint          = last_year + 1
event period             = 按原始 retired_year 判断
```

例如，报告为 2012 年退役的机组在连续时间上于 2013 年边界发生事件，但事件标签仍属于 2012–2015 阶段。2012 年阶段的风险区间至少具有一年正时长。该约定的优点是：

1. 对每个年份采用同一规则，不根据 2000/2012/2016/2021 等研究者设定的切点作特殊处理；
2. 与年度数据“在报告年内处于风险、至该年结束完成退役”的离散观察方式一致；
3. 保留所有报告期内的退役事件，包括同年投产—退役机组；
4. 不改变 Cox 估计框架或任何协变量规格。

局限是：真实退役可能发生在报告年内任何日期，`+1` 仍是约定而非观测到的精确日期。因此论文必须将其写成 annual-time convention，而不是声称掌握了年末退役日期。

### B2. 其他合理方案

**固定年中约定：`retired_year + 0.5`。** 优点是减少把全部退役推到年末的强假设，同样不依赖阶段边界并保留边界事件；缺点是 0.5 仍是任意年中位置，而且投产仍被置于报告年起点，年内信息并未真正恢复。本阶段把它作为辅助敏感性，而不按“结果更好看”选择主模型。

年末和年中约定得到完全相同的四个系数/HR；年中约定的 clustered SE 略大，但三个 post-2012 p 值仍均大于 0.58。这个结果说明主要方向不依赖在报告年度内选择 0.5 还是 1.0 的固定偏移。

**离散时间 hazard 模型**在概念上更贴合年度数据，也能自然保留边界年事件；但它会替换 Cox 估计器和似然，因此不属于本阶段允许的单一维度敏感性，未予估计，也不应用来替代本次 Cox 对照。

不推荐仅对四个边界年人为加极小 `epsilon`。这种处理直接依赖研究者选定的阶段切点，缺少统一的年度时间含义。

---

## C. 敏感性结果

### C1. 总样本对照

| 规格 | Unique contributing units | Retirement events | Unit-period risk intervals |
|---|---:|---:|---:|
| Original 0820：`retired_year` | 4,323 | 952 | 12,344 |
| Boundary-inclusive：`retired_year + 1` | 4,326 | 1,078 | 12,470 |
| 变化 | +3 | +126 | +126 |

### C2. 四阶段主对照

`clustered SE` 是 log-hazard coefficient 的省级聚类稳健标准误；CI 是 HR 的 95% 区间。

| Period | Specification | Period units | Events | Risk intervals | HR | Clustered SE | p value | 95% CI |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2000–2011 | Original 0820 | 2,852 | 443 | 2,852 | 1.263 | 0.126 | 0.063 | [0.987, 1.616] |
| 2000–2011 | Boundary-inclusive | 2,855 | 446 | 2,855 | 1.299 | 0.124 | 0.035 | [1.019, 1.657] |
| 2012–2015 | Original 0820 | 2,904 | 135 | 2,904 | 1.014 | 0.241 | 0.955 | [0.632, 1.627] |
| 2012–2015 | Boundary-inclusive | 2,934 | 165 | 2,934 | 1.117 | 0.181 | 0.542 | [0.783, 1.594] |
| 2016–2020 | Original 0820 | 3,219 | 253 | 3,219 | 1.084 | 0.219 | 0.713 | [0.706, 1.664] |
| 2016–2020 | Boundary-inclusive | 3,293 | 327 | 3,293 | 1.127 | 0.212 | 0.573 | [0.744, 1.708] |
| 2021–2025 | Original 0820 | 3,369 | 121 | 3,369 | 1.124 | 0.230 | 0.613 | [0.715, 1.765] |
| 2021–2025 | Boundary-inclusive | 3,388 | 140 | 3,388 | 1.110 | 0.212 | 0.622 | [0.733, 1.681] |

### C3. 方向、数量级与统计判断

| Period | Original HR | Inclusive HR | Absolute change | Relative change |
|---|---:|---:|---:|---:|
| 2000–2011 | 1.263 | 1.299 | +0.036 | +2.9% |
| 2012–2015 | 1.014 | 1.117 | +0.103 | +10.2% |
| 2016–2020 | 1.084 | 1.127 | +0.043 | +4.0% |
| 2021–2025 | 1.124 | 1.110 | −0.014 | −1.2% |

事实判断：

- 四期方向没有反转，均为 HR > 1；
- 最大相对变化是 2012–2015 的约 10.2%，但 HR 仍仅为 1.117，未改变总体数量级；
- 三个 post-2012 结果的 p 值为 0.542、0.573、0.622，95% CI 均跨 1；
- pre-2012 结果由 p=0.063 变为 p=0.035。这个变化必须如实报告，但不能作为选用年末约定的理由；推荐该编码的依据是年度数据含义和完整保留事件。

对目标表述的判断：**实质结论稳健，但文字应更精确。** 可以写：

> In the boundary-inclusive annual-time specification, the post-2012 period-specific hazard ratios remain statistically indistinguishable from one.

不宜仅凭这些 period-specific p 值把 “no statistically detectable post-2012 retirement acceleration” 写成 post 相对 pre 的正式系数差异结论。若论文需要这种严格含义，应另做与主模型一致的省级聚类稳健跨期 contrast；0820 保存的 `period_difference_tests.csv` 已被 02 审计判定为 model-based、非 cluster-robust diagnostic，不能承担该推断。

### C4. 年中辅助编码

年中方案同样为 4,326 台机组、1,078 个事件、12,470 个区间。四期 HR 与年末方案完全相同：1.299、1.117、1.127、1.110；clustered SE 分别为 0.130、0.204、0.220、0.222，p 值分别为 0.044、0.587、0.588、0.638。它没有改变上述投稿判断。

---

## D. 投稿建议

### D1. 主模型与 Cox 主表

建议把 **boundary-inclusive end-of-reported-year specification** 作为主 Cox 结果，理由是：它为所有年度提供统一时间含义，保留全部可识别退役事件，并避免分析阶段切点机械决定哪些事件消失。建议主表采用 C2 中四行 boundary-inclusive 结果，并明确：

- 4,326 coal units contributing positive-duration intervals；
- 1,078 modeled retirement events；
- 12,470 unit-period intervals；
- HR 对应 1 SD higher pre-policy provincial coal exposure；
- 控制 capacity 和 vintage；省级聚类稳健标准误；左截断 Cox。

现有 4,323/952/12,344 版本应标为 **legacy start-of-reported-year coding / robustness specification**，不应再作为默认主规格。此建议与哪一个版本更显著无关。

### D2. Figure 2

如果采纳新主规格，**Figure 2 需要重画，但本阶段没有修改原图**：

- panel (b) 明确读取 0820 `period_specific_cox.csv`，必须替换为 boundary-inclusive HR 和 CI；
- panel (a) 当前把 2012 年退役编码为 `duration = 2012 - 2012 = 0`。当前 cohort 中有 30 个此类事件，均为 2012 年前投产机组。为了让同一张图采用一致的 annual-time convention，KM panel 也应把 retirement time 政策统一为年末（或在图注中清晰解释不同 convention）。推荐统一重画两面板，而不是只换 panel (b) 数字。

### D3. 论文表述

建议避免把 annual tracker years 写成精确日期。方法部分应直接说明：

> Because GEM reports commissioning and retirement by calendar year rather than exact date, the main specification treats a unit as at risk through its reported retirement year and places retirement at the end of that year. Events are assigned to policy periods by the reported retirement year.

结果部分应强调 post-2012 HR 的不精确性和 CI，而不是把“不显著”解释为已证明没有作用。若保留 “no statistically detectable post-2012 retirement acceleration”，建议紧接着限定其含义为各 post-period HR 未显著偏离 1，并避免暗示已完成 cluster-robust 的 post-versus-pre equality test。

### D4. 本阶段产物与完整性

新产物：

- `code/sensitivity/cox_boundary_sensitivity_0907.py`；
- `result/tables/0907_cox_boundary_sensitivity/cox_boundary_model_results.csv`；
- `result/tables/0907_cox_boundary_sensitivity/cox_boundary_primary_comparison.csv`；
- `result/tables/0907_cox_boundary_sensitivity/boundary_event_audit.csv`；
- `result/tables/0907_cox_boundary_sensitivity/run_metadata.json`；
- `result/figures/0907_cox_boundary_sensitivity/cox_boundary_hr_comparison.png`；
- `result/figures/0907_cox_boundary_sensitivity/cox_boundary_hr_comparison.pdf`。

CSV 校验：12 个 `specification × period` 结果行，无缺失、无重复键。PNG 可正常解析，为 1967 × 1248 RGBA；PDF 文件头有效。`run_metadata.json` 保存了软件版本、模型公式、输入文件 SHA-256、样本计数及原结果复现状态。

本阶段未修改论文 DOCX、原始 GEM 数据、三个原始 survival 脚本、0820 原始结果或 Figure 2 原图。
