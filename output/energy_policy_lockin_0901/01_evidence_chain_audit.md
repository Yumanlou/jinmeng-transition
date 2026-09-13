# 《Designed for Adjustment》论文主张—证据链审计

审计对象：`Designed_for_Adjustment_2026-09-01.docx`  
审计日期：2026-09-02  
审计性质：只读证据链审计；未修改论文或数据，未重新运行任何模型，未增加论文结论。

## 1. 审计口径

本审计区分两个不同问题：

1. **数字一致性**：论文中的数字是否与仓库中已经保存的结果表、图或派生数据一致。
2. **端到端复现性**：能否仅凭当前仓库中的原始数据、当前代码和明确的软件环境，从源数据重新构造分析样本并得到相同结果。

复现性分级如下：

- **完全**：原始输入、构造代码、估计代码、环境说明、运行记录和最终输出均在库内，且链条之间无可见冲突。
- **部分**：主要输入、代码和输出存在，但有硬编码路径、未锁定依赖、外部数据接口、缺少运行日志或其他不能无歧义核验的环节。
- **否**：当前数据与当前代码不能得到论文/结果文件所报告的样本或数字，或关键输入、代码、结果缺失。

本次检查覆盖最新版 DOCX、`output/energy_policy_lockin_0820/` 指定的五个文件、`code/`、与正文结果对应的 `result/` 和 `outputs/`，以及 `data/` 中的 GEM、电力生命周期、能源平衡、资源依赖、可再生能源消纳、煤电可靠性、并网消纳和晋蒙政策文本数据。`outputs/` 中未发现可替代或直接支撑正文 Figure 1–5、Cox 结果和省级固定效应结果的最终证据文件；正文证据主要位于 `result/`。

## 2. 总体结论

论文大部分**已报告数字与现有结果文件一致**，包括 2011—2023 年煤电和风光容量、四阶段 Cox hazard ratio、省级固定效应系数与 pretrend 检验、Figure 3 的晋蒙位置、晋蒙装机数字，以及 Figure 5 的三个全国构成比例序列。

但当前版本不能被认定为“由仓库现有材料完全复现”，存在四类关键问题：

1. **Cox 样本链条冲突**。论文写 4,323 台机组和 952 个 retirement events；现有 Cox 结果文件的四阶段事件数之和确为 952，并与论文 hazard ratio 完全一致。但按当前保存的 GEM 派生数据和当前 survival 脚本的筛选口径，可识别 4,326 台合格机组和 1,078 个 2000—2025 年 retirement events。两组数字无法同时由当前材料成立，且最终 Cox 目录缺少脚本声明应生成的运行日志。冲突原因不能由仓库现有材料判定。
2. **Figure 5 的指标标签与代码字段不一致**。论文把面板 (a) 称为“五类终端用能篮子中的煤炭占比”，但绘图脚本实际使用 `*_consumption_10k_tce_approx` 字段，而省级回归的终端用能结果使用独立的 `*_terminal_*` 字段。68.2% 和 58.8% 与绘图代码及数据一致，但不能据现有代码把它无条件称为“final-use share”。
3. **最新版 DOCX 缺少两张核心结果表的表体**。OOXML 正文中可见 Cox 叙述、Figure 2 和 Cox 表注，但没有包含四个 hazard ratio 的表格主体；省级固定效应结果同样有叙述和表注而缺少系数表体。`manuscript.tex` 和 `result/tables/` 中仍有这些数字，因此这是投稿文档呈现缺失，不是结果文件缺失。
4. **多条链只能部分复现**。若干 Stata 和 survival 脚本含 `/Users/yumanlou/...` 的绝对路径；没有统一的依赖锁文件、Stata 包版本清单或完整运行日志；Wind 数据依赖外部接口；部分文档解析依赖 macOS `textutil`。这些问题不否定已保存结果，但阻止把仓库认定为可直接端到端复现的 replication package。

除此之外，还有两项需要收紧文字：省级项目生命周期回归实际使用的是标准化的政策前 thermal-capacity exposure（`post12_pretherm_z`），正文概括为“coal exposure”容易与五类终端用能煤炭暴露混淆；Figure 3 实际只画出煤电存量、可再生能源消纳和资源依赖三项，并没有把 reliability、utilization/curtailment、项目管线等“整组约束变量”都画出或进行联合检验。

## 3. 主要定量与实证主张逐项审计

### 3.1 全国煤电与风光资产轨迹（重点 A）

**论文原始表述**

> “China's operating coal fleet nevertheless expanded from about 686 GW in 2011 to 1,143 GW in 2023.”

> “Operating coal capacity rose from 686.3 GW in 2011 to 1,142.9 GW in 2023, while operating wind and solar capacity rose from 43.6 GW to 722.6 GW.”

> “Coal additions remained positive throughout the period, and observed retirements remained below commissioning in every year.”

**对应章节**：Abstract；Introduction；“Direct asset evidence”；“Results: asset stocks and flows”；direct-asset evidence table；Figure 1。

**证据链**

- 原始数据：
  - `data/gem_power_project_lifecycle/source/GEM_GCPT_January_2026.xlsx`
  - `data/gem_power_project_lifecycle/source/GEM_GWPT_February_2026.xlsx`
  - `data/gem_power_project_lifecycle/source/GEM_GSPT_February_2026.xlsx`
- 数据构造脚本：`code/build_gem_power_project_lifecycle_0721.py`
- 派生数据：
  - `data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv`
  - `data/gem_power_project_lifecycle/gem_province_year_lifecycle_2000_2023.csv`
  - `data/gem_power_project_lifecycle/gem_lifecycle_coverage.csv`
  - `data/gem_power_project_lifecycle/source_metadata.json`
- 统计/制图脚本：
  - `code/plot_energy_policy_asset_lifecycle_0822.py`
  - `code/plot_energy_policy_evidence_figures_0822.py`
- 最终输出：
  - `result/figures/energy_policy_lockin_0820/Figure_1_asset_lifecycle.png`
  - 同名 PDF
  - 最新 DOCX 中 Figure 1

**核对结果**

| 项目 | 当前派生数据 | 论文 | 判断 |
|---|---:|---:|---|
| 2011 operating coal stock | 686.3063 GW | 686.3 GW | 一致 |
| 2023 operating coal stock | 1,142.8918 GW | 1,142.9 GW | 一致 |
| 2011 operating wind + solar | 43.5748 GW | 43.6 GW | 一致 |
| 2023 operating wind + solar | 722.5843 GW | 722.6 GW | 一致 |
| 2011 coal commissioned | 62.0560 GW | 62.1 GW | 一致 |
| 2023 coal commissioned | 48.6280 GW | 48.6 GW | 一致 |
| 2011 coal retired | 4.1540 GW | 4.2 GW | 一致 |
| 2023 coal retired | 3.3278 GW | 3.3 GW | 一致 |
| 2000—2023 各年 retirements < commissioning | 当前派生序列每年均成立 | 正文称 every year | 一致 |

**是否完全复现**：**部分**。GEM 原始工作簿、构造脚本、派生面板、元数据和图均在库内；但未提供统一环境锁文件和该次构造的完整运行日志。原始数据为 2026 年当前快照的回溯重建，而非逐年 vintage archive。

**推断边界**：正文把这些数字用于说明存量扩张和观察到的退役不足，证据允许。它们不能单独证明政策导致或未导致装机变化。GEM 元数据已经提示：缺失 start year 会使早期 stock 成为下界；当前快照也可能受退役项目回填和状态修订影响。正文基本披露了这一限制。

**来源/代码问题**：无数字冲突。西藏在煤电项目数据中缺失并被资产面板按零处理；正文已说明这一编码，但它应继续被理解为项目数据库中的“未识别到煤电项目”，而不是独立验证的真实零值。

### 3.2 4,323 台机组与 952 个退役事件（重点 B）

**论文原始表述**

> “The current release identifies 4,323 coal units and 952 retirement events.”

**对应章节**：“Direct asset evidence”；Cox 表注和样本说明。

**证据链**

- 原始数据：`data/gem_power_project_lifecycle/source/GEM_GCPT_January_2026.xlsx`
- 构造脚本：`code/build_gem_power_project_lifecycle_0721.py`
- 派生数据：`data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv`
- survival 脚本：
  - `code/coal_retirement_survival.py`
  - `code/coal_retirement_survival_segmented.py`
  - `code/coal_retirement_survival_final_0820.py`
- 最终结果：
  - `result/tables/0820_coal_retirement_survival_final/period_specific_cox.csv`
  - `result/tables/0820_coal_retirement_survival_final/period_difference_tests.csv`
  - `result/figures/energy_policy_lockin_0820/Figure_2_retirement_evidence.png`

**核对结果**

- `period_specific_cox.csv` 中四阶段 event 数为 443、135、253、121，合计 **952**；因此论文的 952 与保存的最终结果文件一致。
- 同一结果文件报告 `n_intervals = 12,344`，与 `manuscript.tex` 的 Cox 表注一致。
- 但对当前 `gem_china_project_units_2026_snapshot.csv` 按当前 survival 脚本的保存口径进行只读筛选，得到 **4,326** 台合格煤电机组和 **1,078** 个 2000—2025 年退役事件；事件分段为 446、165、327、140。
- 当前合格记录及 retirement 记录的 GEM unit ID 均未显示由重复 ID 造成的多计。
- `gem_lifecycle_coverage.csv` 另报告 6,520 条中国煤电原始行、4,537 条 active/historical 行；这些是覆盖统计，不等同于 Cox 最终样本，不能用来调和上述 4,323/4,326 冲突。

**是否完全复现**：**否**。论文数字与最终结果 CSV 一致，但不能由当前派生数据和当前保存代码无歧义复得。最终结果目录也缺少 `coal_retirement_survival_final_0820.py` 声明应生成的运行日志，无法确认当时实际读取的数据版本、筛选过程或软件输出。

**推断边界**：样本计数本身是描述性事实，不涉及因果推断；问题在于版本可追溯性。

**来源/代码问题**：这是当前证据链最严重的不一致。不能根据现有材料猜测是旧数据快照、旧筛选代码、手工排除还是其他原因。投稿前应先恢复生成 4,323/952 的确切输入与日志，或使论文、数据和代码统一。

### 3.3 分阶段 Cox survival model 与退役加速（重点 C、D）

**论文原始表述**

> “The period-specific hazard ratios are 1.26 before 2012, 1.01 in 2012–2015, 1.08 in 2016–2020, and 1.12 in 2021–2025.”

> “There is no detectable post-2012 acceleration in coal retirement.”

> “The estimates do not show a statistically detectable increase in retirement hazards after 2012.”

**对应章节**：Abstract；Introduction；“Direct asset evidence”；“Results: retirement survival”；Figure 2；Cox 结果表及表注。

**证据链**

- 原始与派生数据：同 3.2，并使用省级政策前暴露变量。
- 统计脚本：`code/coal_retirement_survival_final_0820.py`；较早版本见另外两个 survival 脚本。
- 最终输出：
  - `result/tables/0820_coal_retirement_survival_final/period_specific_cox.csv`
  - `result/tables/0820_coal_retirement_survival_final/period_difference_tests.csv`
  - `result/figures/energy_policy_lockin_0820/Figure_2_retirement_evidence.png`

**数字一致性**

| 阶段 | 结果文件 HR | p 值 | events | 论文显示 | 判断 |
|---|---:|---:|---:|---:|---|
| 2000—2011 | 1.263200 | 0.062933 | 443 | 1.26；p=0.063 | 一致 |
| 2012—2015 | 1.013762 | 0.954860 | 135 | 1.01；p=0.955 | 一致 |
| 2016—2020 | 1.083647 | 0.713436 | 253 | 1.08；p=0.713 | 一致 |
| 2021—2025 | 1.123724 | 0.612606 | 121 | 1.12；p=0.613 | 一致 |

模型脚本控制机组容量和 vintage，并按省聚类标准误；正文对此描述一致。Figure 2 左图以 2012 年初仍在运的 2,409 台机组为 cohort，当前数据和制图口径可以复得该 cohort 数；图中 high-exposure 1,390、low-exposure 1,019，合计 2,409。

**是否完全复现**：**否**。HR 与保存结果一致，但 3.2 的样本/事件冲突意味着当前数据—代码链不能证明这些 CSV 是由当前快照生成。脚本还含用户特定绝对路径，缺少运行日志和依赖版本记录。

**推断边界**

- “no detectable acceleration”是对“不显著”的谨慎表述，优于“没有加速”或“政策无效”；正文总体没有把接近 1 的 HR 解释成政策无效。
- 但各阶段 HR 的单独 p 值检验的是该阶段 HR 是否等于 1，并不直接检验“post-2012 HR 是否高于 pre-2012 HR”。`period_difference_tests.csv` 提供阶段差异检验，但脚本明确说明这些差异检验使用未聚类模型协方差，并非省级 cluster-robust covariance；正文没有报告这些差异 p 值是适当的。
- 观察性 survival model 不能排除机组构成、未观测政策、状态更新和选择性退役的影响。现有结果只支持“未检测到与暴露相关的更快退役”，不支持“政策没有影响退役”。正文的限制说明基本合格。

**来源/代码问题**

- 最新 DOCX 中未发现包含四行 HR 的 Cox 表体；只有正文数字、Figure 2 和表注。`manuscript.tex` 中表体仍存在。
- `period_difference_tests.csv` 的非聚类差异检验不应被升级为主要显著性证据。
- 4,323/952 与当前数据/代码不一致，导致本项不能被认证为端到端复现。

### 3.4 省级项目生命周期结果

**论文原始表述**

> “At the province-year level, post-2012 coal exposure is not significantly associated with coal additions, retirements, net additions, or the coal share of operating capacity.”

**对应章节**：“Results: asset stocks and flows”；支持性项目生命周期回归。

**证据链**

- 原始/派生数据：GEM 三个项目工作簿及 `gem_province_year_lifecycle_2000_2023.csv`。
- 数据构造脚本：`code/build_gem_power_project_lifecycle_0721.py`
- 统计脚本：`code/policy_eval_gem_project_lifecycle_0721.do`
- 最终输出：`result/tables/0721_gem_project_lifecycle/Table_0721_GEM_Project_Lifecycle.csv`

**核对结果**

与正文直接相关的结果均不显著：IHS coal additions 系数 -0.1689（p=0.689）、IHS coal retirements -0.3820（p=0.228）、coal net additions -154.0 MW（p=0.345）、coal stock share 0.0505（p=0.162）。因此“不显著”的方向与结果文件一致。

**是否完全复现**：**部分**。原始数据、构造脚本、Stata 脚本和输出表均存在；但 Stata 路径与包环境未锁定，缺少本次运行日志。

**推断边界**：结果支持“在该规格下未检测到关联”，不能证明各省煤电项目调整完全相同，也不能证明政策没有影响。

**来源/代码问题**：估计脚本使用的交互项是 `post12_pretherm_z`，输出标签为 `Post2012_x_PreThermal`，即政策前 thermal-capacity exposure。正文用“coal exposure”概括，容易使读者误以为它与省级能源结果使用的 2008—2011 年五类终端用能煤炭份额是同一 exposure。应明确为“pre-policy thermal-capacity exposure”或给出两者关系。

### 3.5 省级固定效应、连续暴露与趋势稳健性（重点 E、F）

**论文原始表述**

> “More coal-exposed provinces experienced larger post-2012 declines in coal-use intensity and in coal's share of the five-energy final-use basket.”

> “The baseline estimates are -0.289 for five-energy intensity, -0.426 for coal-terminal-use intensity, and -0.250 for coal's share of the five-energy basket.”

> “The coal-share outcome has comparatively clean pre-policy dynamics, whereas the intensity outcomes are sensitive to pre-trends and province-specific linear trends.”

> “Once province-specific linear trends are added, both intensity estimates are statistically indistinguishable from zero.”

**对应章节**：Abstract；“Provincial supporting evidence”；“Results: provincial supporting evidence”；支持性固定效应表和 event-study 讨论。

**原始数据与构造链**

- 基础面板：`data/final_data.1.3.4_did.csv`
- 能源平衡原始表：
  - `data/append_0518/数据模板命名1.csv`
  - `data/append_0518/数据模板 5.csv`
- 能源构造脚本：`code/build_energy_balance_panel.py`
- 扩展面板脚本：`code/build_append_0518_full_panel.py`
- 中间/最终分析面板包括：
  - `data/final_data.1.3.4_did_energy_0518.csv`
  - `data/final_data.1.3.4_did_full_0518.csv`
  - `data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_0718.csv`
  - 基线脚本所读取的相应 `...greencredit_0716.csv` 版本
- 统计脚本：
  - `code/policy_eval_manuscript_revision_0718.do`
  - `code/policy_eval_trend_robustness_0820.do`
- 最终输出：
  - `result/tables/0718_manuscript_revision/Table_0718_1_Baseline_CI_Windows.csv`
  - `result/tables/0718_manuscript_revision/Table_0718_3_Event_Studies.csv`
  - `result/tables/0718_manuscript_revision/Table_0718_5_Robustness.csv`
  - `result/tables/0820_trend_robustness/Table_0820_Trend_Robustness.csv`

**变量构造**

`build_energy_balance_panel.py` 将煤、油品、LPG、天然气和电力按脚本中的近似折标系数转为万吨标准煤，构造五类能源合计、煤炭份额和相对 GDP 的强度；政策前暴露为 2008—2011 年煤炭份额的省级均值。`build_append_0518_full_panel.py` 把 `energy5_int`、`coalterm_int`、`coalshare5` 等别名接入扩展面板。最终面板为 31 省、2000—2023 年、744 个 province-year；终端用能结果止于 2022 年。

**数字一致性**

| 结果 | baseline 系数 | baseline p | pretrend joint p | 加省线性趋势系数 | 趋势规格 p | 论文判断 |
|---|---:|---:|---:|---:|---:|---|
| five-energy intensity | -0.289455 | 0.021392 | 0.051703 | -0.122507 | 0.06155 | 数字和“敏感”判断一致 |
| coal terminal-use intensity | -0.426185 | 0.000006 | 0.041491 | -0.057399 | 0.19254 | 一致 |
| coal share of five-energy basket | -0.249505 | 0.002501 | 0.840102 | +0.089692 | 0.20033 | baseline/pretrend 数字一致；趋势规格方向改变且不显著 |
| SO₂ | -72.5887 | 0.000935 | 0.052515 | +28.6158 | 0.00545 | 结果表存在；正文没有把趋势后反向结果作为核心结论 |

baseline 的三个主要系数和 p 值与论文完全一致。能源强度在省线性趋势规格下 p≈0.062，严格说是 5% 水平不显著但接近阈值；“statistically indistinguishable from zero”在预设 5% 水平下成立，不过应避免把它表述成“没有效应”。煤炭终端用能强度在趋势规格下明显不显著。

连续暴露 event-study 以 2011 年为省略期，时间分组为 `<=2008`、2009、2010、2012、2013、2014、2015、`>=2016`，不是每一年均单列的全动态路径。煤炭份额 pretrend joint p=0.840，支持“未检测到明显 pretrend”；两个强度结果的 p≈0.052 和 0.041 表明平行趋势证据较弱。

**是否完全复现**：**部分**。原始能源文件、构造脚本、最终分析面板、Stata do-file 和结果 CSV 均存在，且结果文件内部一致；但 do-file 含用户特定绝对路径，`reghdfe`、`outreg2`、`coefplot` 等 Stata 包版本未锁定，也未保存完整可核对日志。

**推断边界**

- 该设计没有未受政策影响的省份，识别依靠政策前煤炭暴露的连续差异；结果是暴露异质性的条件相关，不是全国政策平均处理效应。
- “more coal-exposed provinces experienced larger declines”可以作为规格内的描述性关联，但不应写成政策导致这些下降。正文多处称其为 supporting/diagnostic evidence，并明确不是清洁因果设计，边界基本合格。
- “coal-share dynamics comparatively clean”只能理解为该 event-study 未拒绝共同 pretrend；p=0.840 不证明平行趋势为真，而且 `<=2008` 与 `>=2016` 使用合并时间箱，检验力和动态分辨率有限。
- baseline coal-share 结果在省线性趋势规格中变为正且不显著，因此如果把“煤炭份额下降”称为对趋势完全稳健，会超过证据。当前正文主要强调 intensity 的趋势敏感性，但也应让读者看到 coal-share 的趋势规格变化。

**来源/代码问题**：最新版 DOCX 中未发现支持性省级结果表的系数表体；`manuscript.tex` 和结果 CSV 中数字完整。能源折标系数写在脚本中，但没有单独的数据字典或版本化官方换算依据文件；这影响可追溯性，不构成当前数字与结果文件的冲突。

### 3.6 资源依赖、可再生能源消纳与可靠性约束（重点 I）

**论文原始表述**

> “The relevant constraints include resource dependence, renewable-consumption obligations, coal-unit reliability, grid absorption, and the existing project pipeline.”

> “Figure 3 plots this bundle descriptively.”

> “Shanxi and Inner Mongolia both combine large coal fleets with below-median renewable-consumption performance, but they differ markedly in pre-policy resource dependence.”

**对应章节**：“Constraint variables”；“Results: constraint typology”；Figure 3；Discussion。

**证据链**

#### 资源依赖

- 原始/准原始数据：`data/wind_resource_dependency/wind_resource_dependency_panel_2000_2023.csv` 及其 codebook/coverage 文件。该面板由 Wind 指标拉取得到，仓库保存的是整理后的查询结果，而不是完整、可离线重放的原始 API 响应。
- 构造脚本：
  - `code/fetch_wind_resource_dependency.py`
  - `code/build_resource_dependence_v2_0716.py`
  - `code/merge_resource_dependency_panel.py`
- 构造：2008—2011 年 mining employment share、coal-mining asset share、resource-tax share 分别标准化后取均值；至少有两个分量才计算综合 index，随后在省内跨年重复。
- 输出/图：最终扩展面板；`Figure_3_constraint_typology.png`。

资源依赖 index 在当前最终面板中覆盖 30 省、720 个 province-year；西藏缺失。分项覆盖不完全相同，因此各省综合 index 可能由不同数量的分量构成，跨省比较应保留这一限制。

#### 可再生能源消纳

- 原始文件：`data/nea_renewable_monitoring/source_docs/` 下 2015—2023 年 NEA 年度 doc/docx。
- 构造脚本：`code/build_nea_renewable_consumption_panel_0718.py`
- 派生数据：`data/nea_renewable_consumption/` 下年度面板、coverage 和 source metadata。
- 当前最终面板覆盖：31 省、2015—2023 年、279 个观测。
- Figure 3 使用各省 2020—2023 年 renewable consumption share 的均值。

#### 煤电可靠性

- 原始文件：`data/nea_power_reliability/source_pdfs/` 下 2018—2023 年 NEA PDF。
- 构造脚本：`code/build_nea_coal_reliability_panel_0718.py`
- 派生数据：`data/nea_coal_reliability/` 下 panel/coverage/source metadata。
- 当前最终面板：coal-unit operating factor 和 standby factor 各 180 个观测、30 省、2018—2023；coal-unit utilization hours 90 个观测、30 省、2018—2020。

#### 并网消纳与弃风弃光

- NEA 文档及 `code/clean_nea_renewable_utilization.py`；Wind 补充链见 `code/fetch_wind_grid_absorption.py` 和对应 derived panel/codebook。
- 当前最终面板中的 wind/solar utilization 或 curtailment 指标合计覆盖 124 个 province-year、31 省、2020—2023。
- Wind 链需要外部服务，仓库不足以离线重放全部拉取过程。

#### 项目管线

- GEM 原始工作簿及 `code/build_gem_power_project_lifecycle_0721.py`。
- 派生数据：`data/gem_power_project_lifecycle/gem_province_current_pipeline_2026.csv`。

**Figure 3 数字核对**

Figure 3 的实际绘图变量仅有：横轴 2020—2023 年平均煤电存量，纵轴 2020—2023 年平均可再生能源消纳比例，颜色为政策前资源依赖 index。当前数据的中位数为煤电存量 28.8485 GW、可再生能源消纳 28.0%。晋蒙数值为：

| 省份 | 2020—2023 平均煤电存量 | 平均可再生能源消纳 | 资源依赖 index | 相对中位数 |
|---|---:|---:|---:|---|
| Shanxi | 69.6120 GW | 24.075% | 3.05577 | 高煤电、低于消纳中位数 |
| Inner Mongolia | 101.9645 GW | 24.300% | 1.05489 | 高煤电、低于消纳中位数 |

因此正文关于两省 Figure 3 位置及资源依赖差异的描述与数据一致。

**是否完全复现**：**部分**。NEA 公开文档、主要构造脚本、派生面板和图在库内；但两个 NEA 文档解析脚本调用 macOS `textutil`，当前 Windows 环境不能原样执行；Wind 数据需要外部/专有接口；未提供统一运行环境和完整日志。

**推断边界**

- Figure 3 是描述性三变量 typology，不识别 constraint 对退役、投资或转型结果的因果效应。正文明确称其 descriptive，边界基本合格。
- “Figure 3 plots this bundle”超过图的实际信息量。图中没有显示 coal reliability、utilization/curtailment、项目 pipeline，也没有把 mining employment、assets 和 resource tax 三个资源依赖分量分别显示。更准确的说法应是“Figure 3 plots three observable dimensions of this bundle”。
- reliability 等变量开始年份晚且覆盖窗口短，不能用于解释 2012 年后的完整动态；目前也没有与正文 Cox 或省级 FE 主结论对应的最终回归表证明这些变量是机制。

**来源/代码问题**：公共 NEA 来源文件较完整；Wind 原始调用结果无法在无外部权限情况下完整重建。资源依赖 index 的分量可用性不完全一致，需要在解释跨省颜色差异时保留测量可比性限制。

### 3.7 Shanxi 与 Inner Mongolia 比较（重点 H）

**论文原始表述**

> “By 2023, Shanxi had 74.3 GW of operating coal capacity and 42.8 GW of wind and solar, compared with 115.1 GW and 82.1 GW in Inner Mongolia.”

> “After 2012, Inner Mongolia exhibits more green-finance and clean-coal policy language, while differences in renewable and pollution-control language are not statistically stable.”

> “The comparison is descriptive rather than causal.”

**对应章节**：“Shanxi–Inner Mongolia comparison”；Figure 4；case-comparison results；Discussion。

**装机证据链**

- 原始/派生数据和构造脚本：同 3.1。
- 制图脚本：`code/plot_energy_policy_evidence_figures_0822.py`
- 输出：`result/figures/energy_policy_lockin_0820/Figure_4_case_lifecycles.png` 及 PDF。

2023 年当前派生数据为：Shanxi coal 74.3220 GW、wind+solar 42.7652 GW；Inner Mongolia coal 115.1320 GW、wind+solar 82.0668 GW。均与论文四舍五入数字一致。

**政策文本证据链**

- 原始政策文档清单/文本：
  - `data/policy_texts/shanxi_policy_documents_2000_2023.csv`
  - `data/policy_texts/nmg_policy_documents_2000_2023.csv`
- 构造脚本：`code/build_policy_text_indices.py`
- 派生面板：`data/policy_texts/jinmeng_policy_text_year_panel_2000_2023.csv`
- 统计脚本：`code/policy_eval_0518_full_chain.do`
- 最终输出：`result/tables/0518_full_chain/Table_0518_7_JinMeng_Policy_Text_Path.txt`

输出表中，Inner Mongolia × post-2012 的 green-finance language 为正（per-10k 0.3062，带一星；document share 0.0382，带两星），clean-coal language 为正（per-10k 9.3511、document share 0.1361，均三颗星）；pollution-control 和 renewable language 的两个口径均不显著。正文概括与结果文件一致。

**是否完全复现**：**部分**。政策文本数据、索引构造脚本、Stata 脚本和最终表存在；但政策文档抓取依赖外部网页状态，未形成可完全离线验证的网页快照链，Stata 环境也未锁定。回归 N=44，而两省 2000—2023 的完整平衡面板应为 48；现有原始 CSV 显示 Shanxi 从 2002 年开始，早期覆盖不平衡是可见原因之一，但不能据此猜测全部样本排除过程。

**推断边界**：两省比较只有两个案例，政策文本指标反映词频/文档占比，不等于政策强度、执行强度或实际效果。正文明确称描述性而非因果，并称 renewable/pollution-control 差异“不稳定”，与证据边界相符。不能由此断言 Inner Mongolia 的能源转型优于 Shanxi，或文本变化导致装机变化。

**来源/代码问题**：装机数字链清楚；文本链存在早期年份不平衡和外部抓取可重复性限制。正文未报告 N=44 和早期覆盖差异，读者仅凭正文无法发现。

### 3.8 全国构成变化与 Figure 5（重点 F、G）

**论文原始表述**

> “Coal's share of the five-energy final-use basket fell from 68.2% in 2006 to 58.8% in 2022.”

> “The thermal share of installed capacity fell from 77.6% in 2006 to 47.6% in 2023, while the thermal share of generation fell from 80.9% to 65.6%.”

**对应章节**：“Results: annual composition shares”；Figure 5；Discussion。

**证据链**

- 能源原始数据、构造脚本和面板：同 3.5。
- 电力装机/发电原始 Wind 导出和扩展面板构造：`code/build_append_0518_full_panel.py`。
- 制图脚本：`code/plot_energy_policy_evidence_figures_0822.py` 中 `plot_annual_composition_shares()`。
- 最终输出：`result/figures/energy_policy_lockin_0820/Figure_5_annual_composition_shares.png` 及 PDF；最新版 DOCX Figure 5。

**数字一致性**

按绘图脚本实际使用字段和全国加总方法重新读取现有面板：

| 指标 | 起点 | 终点 | 论文 | 判断 |
|---|---:|---:|---|---|
| 脚本所算五类 `consumption` 煤炭份额 | 68.2109%（2006） | 58.8413%（2022） | 68.2% → 58.8% | 数字一致 |
| thermal installed-capacity share | 77.5729%（2006） | 47.6001%（2023） | 77.6% → 47.6% | 一致 |
| thermal generation share | 80.9176%（2006） | 65.6086%（2023） | 80.9% → 65.6% | 一致 |

**是否完全复现**：**部分**。现有派生面板、绘图代码和图可以对应，且图中数字一致；但上游 Wind 获取、软件环境和日志不完整。

**推断边界**

- thermal capacity/generation share 的下降不等于煤电绝对量下降；Figure 1 已显示煤电绝对存量上升。正文将“composition”与“stock”区分，边界合格。
- non-thermal 不能与 renewables 画等号，electricity 也不能直接等同 clean energy。正文表注已作提醒。

**来源/代码问题：指标命名冲突**

Figure 5 面板 (a) 的绘图代码使用：

- `coal_consumption_10k_tce_approx`
- `oil_consumption_10k_tce_approx`
- `lpg_consumption_10k_tce_approx`
- `gas_consumption_10k_tce_approx`
- `electricity_consumption_10k_tce_approx`

而省级“终端用能”结果使用独立的 `*_terminal_*` 字段及其别名 `energy5_int`、`coalterm_int`、`coalshare5`。因此，68.2%→58.8% 是**现有 Figure 5 consumption 字段的正确计算结果**，但当前代码不能支持把它直接标为“five-energy final-use basket”。在字段定义得到外部核实前，应视为文字—代码不一致，而不是自行推断两组字段等价。

### 3.9 31 省、2000—2023 面板及数据覆盖

**论文原始表述**

> “We assemble a 31-province panel for 2000–2023.”

> “The final-use energy outcomes end in 2022.”

**对应章节**：Abstract；Data；Provincial supporting evidence。

**证据链**：基础面板和扩展链同 3.5；资源、NEA 和 GEM 数据通过各自 merge/build 脚本接入最终面板。

**核对结果**：最终分析面板 744 行，即 31×24，年份为 2000—2023；能源终端用能核心结果的有效期止于 2022。该主张与当前面板一致。

**是否完全复现**：**部分**。基础和最终面板存在，合并脚本可追踪，但长链涉及 Wind 外部接口、多个时间戳版本和未锁定环境。

**推断边界与覆盖问题**：744 行只是面板骨架完整，不代表所有变量 744 行均非缺失。资源依赖、renewable consumption、reliability 和 grid absorption 的起始年份、覆盖省份不同；论文已部分披露，但“31-province panel”不应被理解为每个 constraint 指标都有完整 31×24 覆盖。

## 4. Figure 1–5 专项审计（重点 G）

最新版 DOCX 内嵌的五幅图与 `result/figures/energy_policy_lockin_0820/` 中对应 PNG 在缩放后视觉内容一致；DOCX 对图像进行了重采样，因此文件哈希和像素尺寸不同，不构成内容版本冲突。

| 图 | 数据与脚本 | 最终输出 | 与 DOCX | 数字/内容一致性 | 主要审计问题 |
|---|---|---|---|---|---|
| Figure 1 | GEM lifecycle；`build_gem_power_project_lifecycle_0721.py`；`plot_energy_policy_asset_lifecycle_0822.py` | `Figure_1_asset_lifecycle.png/.pdf` | 同图的重采样版本 | 686.3、1,142.9、43.6、722.6 及年度流量一致 | 当前快照回溯数据；早期 stock 可能为下界 |
| Figure 2 | GEM unit snapshot；survival final 脚本；`period_specific_cox.csv` | `Figure_2_retirement_evidence.png/.pdf` | 同图的重采样版本 | HR、CI、2,409 cohort 与现有结果/数据一致 | HR 结果的 4,323/952 样本无法由当前快照与代码复得；缺运行日志 |
| Figure 3 | 2020—2023 平均煤电 stock、renewable consumption、pre-policy resource index；evidence figure 脚本 | `Figure_3_constraint_typology.png/.pdf` | 同图的重采样版本 | 晋蒙象限和数值一致 | 只画三项，不是全部 constraint bundle；晚期覆盖和 Wind 外部依赖 |
| Figure 4 | GEM 晋蒙 lifecycle；evidence figure 脚本 | `Figure_4_case_lifecycles.png/.pdf` | 同图的重采样版本 | 2023 晋蒙四个装机数字一致 | 仅描述性，不能从两省路径识别政策效果 |
| Figure 5 | 扩展省级面板；`plot_annual_composition_shares()` | `Figure_5_annual_composition_shares.png/.pdf` | 同图的重采样版本 | 三组起止比例均一致 | 面板 (a) 实用 `consumption` 字段，却标为 final-use；上游 Wind/环境链不完整 |

## 5. A–I 重点问题结论对照

| 重点 | 结论 | 严重性 |
|---|---|---|
| A. 686.3 GW → 1,142.9 GW | 与 GEM 派生面板、Figure 1 和表格完全一致；属于当前快照回溯的存量描述 | 低；保留快照/下界限制 |
| B. 4,323 units / 952 events | 与保存 Cox 结果的 952 一致，但当前数据+代码为 4,326/1,078，无法复现 | **高** |
| C. 各阶段 Cox HR | 1.263/1.014/1.084/1.124 及 p 值与结果 CSV 一致 | **高**：样本链冲突、表体缺失、日志缺失 |
| D. post-2012 retirement acceleration | “未检测到”符合现有结果和非因果边界；不能改写为“没有加速”或“政策无效” | 中高 |
| E. provincial FE / continuous exposure | baseline、pretrend、趋势规格数字均与结果表一致；只能视为关联，且趋势敏感 | 中；DOCX 表体缺失、环境未锁定 |
| F. coal share / energy intensity | FE 结果数字一致；强度 pretrend/趋势较弱；Figure 5 的 coal share 另有 consumption/final-use 标签冲突 | **高**（Figure 5 命名）；中（FE 推断） |
| G. Figure 1–5 | 五图均有 PNG/PDF，DOCX 内嵌内容与之相同 | Figure 2、5 有高优先级证据链问题 |
| H. Shanxi / Inner Mongolia | 装机和政策文本结果与数据/输出一致；样本 N=44、早期覆盖不平衡；只能描述性比较 | 中 |
| I. resource dependence / renewable consumption / reliability 等 | 数据源、构造脚本和覆盖可追踪；Figure 3 只用其中三维，不能声称整组约束被图示或检验 | 中高 |

## 6. 文件缺失、来源不明确与代码—文字不一致清单

### 6.1 必须优先解决

1. **恢复 Cox 的确切分析版本**：当前仓库需要能说明 4,323 台机组、952 个事件和 12,344 个 unit-period intervals 如何从某一明确输入生成。现有 2026 snapshot 与当前代码给出不同计数。
2. **补回最新版 DOCX 的两张结果表体**：Cox hazard-ratio 表和省级 fixed-effects/continuous-exposure 支持表在 `manuscript.tex` 与结果目录中有数字，但 2026-09-01 DOCX 正文没有表体。
3. **核实并统一 Figure 5 面板 (a) 的变量定义**：代码为 `consumption`，正文/图注为 `final-use`；在没有数据字典证明两者等价前，不能视为同一指标。

### 6.2 需要在文字或复现材料中澄清

4. 项目生命周期省级回归的 exposure 是 `pretherm_z`，不是正文其他部分的五能源煤炭份额 exposure。
5. Figure 3 只呈现煤电 stock、renewable consumption 和 resource dependence；reliability、grid absorption、curtailment、pipeline 未在该图中展示，也没有形成正文核心机制回归。
6. 晋蒙政策文本回归 N=44，早期覆盖不平衡；正文没有披露这一样本事实。
7. 资源依赖综合指标在至少两个分量可得时计算，各省分量数可能不同；西藏缺失。
8. 约束变量不是 2000—2023 全时段覆盖：renewable consumption 自 2015 年，reliability 自 2018 年，grid/utilization 主要自 2020 年。

### 6.3 复现基础设施缺口

9. 多个主结果 Stata/survival 脚本含用户特定 macOS 绝对路径 `/Users/yumanlou/...`，不能在当前项目根目录直接运行。
10. 仓库未发现统一 `requirements.txt`、`pyproject.toml`、conda lock、Stata 版本/用户包快照、Makefile 或一键 replication 说明。
11. Cox 最终结果目录缺少脚本声明的运行日志；省级主结果目录也没有足以证明该 CSV 生成过程的完整可读日志。
12. 两个 NEA 文档构造脚本依赖 macOS `textutil`；当前 Windows 环境不能原样执行。
13. Wind 资源依赖和并网消纳链需要外部/专有数据访问；仓库有派生 CSV 和 codebook，但不足以从原始 API 响应离线重放。
14. GEM 数据使用 2026 年当前快照回溯历史，未保存用于比较的逐年 vintage archive；早期存量和历史状态受当前版本记录完整性约束。

## 7. 最终审计判断

就“论文数字是否与现有结果文件一致”而言，除样本版本和指标标签问题外，主要报告值高度一致：资产存量与流量、四阶段 Cox HR、省级 FE/pretrend/trend 系数、Figure 3 晋蒙位置、Figure 4 装机数字、政策文本比较和 Figure 5 起止比例均能在现有输出或派生面板中找到直接对应。

就“是否可以从仓库现有材料完全复现”而言，结论是**不能**。最直接的否决项是 Cox 当前数据/代码与论文样本计数不一致；其余主结果多为“部分复现”，原因包括绝对路径、依赖未锁定、运行日志缺失、外部 Wind 接口和平台特定文档工具。

就“表述是否超过证据允许的推断边界”而言，论文整体已经采用 diagnostic、supporting、descriptive、no detectable 等谨慎措辞，未把观察性结果直接升级为因果政策效果。但以下三种表达仍超过或混淆了现有证据：把 Figure 5 的 `consumption` 指标称为 final-use；把 `pretherm_z` 回归笼统称为与其他部分相同的 coal exposure；声称 Figure 3 展示整组 constraint variables。Cox 的“no detectable acceleration”可以保留，但前提是先解决分析样本版本冲突，并始终避免改写为“no acceleration”或“policy ineffectiveness”。
