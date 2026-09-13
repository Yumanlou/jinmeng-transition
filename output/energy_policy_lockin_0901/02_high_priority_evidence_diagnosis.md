# Energy Policy 投稿终审高优先级证据诊断

诊断对象：`Designed_for_Adjustment_2026-09-01.docx` 及对应代码、派生数据和保存结果  
诊断日期：2026-09-07  
诊断性质：只读核对。未修改论文、代码、数据或已有结果，未重新估计模型。

## 1. 结论摘要

本轮精确计数更正了 `01_evidence_chain_audit.md` 对 Cox 样本冲突的判断，同时确认了 Figure 5 标签冲突和 DOCX 缺表问题。

1. **4,323 台机组、952 个事件和 12,344 个 unit-period observations 可由当前数据和当前最终脚本同时复得，并非数据版本冲突。**4,326 是通过初始资格筛选的记录数，其中 4,323 台至少形成一个正时长风险区间；1,078 是合格记录中 2000—2025 年全部退役年份的计数，模型区间构造排除了四个阶段起始年的 126 个退役记录，故模型事件数为 952。
2. **Cox 仍有一个具体的区间编码问题。**2000、2012、2016、2021 年的退役记录分别为 3、30、74、19 个。脚本令阶段内区间起点为阶段首年、区间终点为退役年，并删除 `interval_end <= interval_start` 的区间，所以这些边界年事件全部未计入 Cox event。论文中的 952 应准确称为 modeled retirement events，而不是当前合格记录中观察到的全部退役事件。
3. **Figure 5 panel (a) 的 68.2%→58.8% 是五个 `consumption` 字段的构成，不是 `terminal`/final-use 构成。**原始能源平衡项目“能源消费”和“终端消费量”在数据和代码中是两套不同字段。按同一全国汇总法使用 `*_terminal_*` 字段，煤炭份额为 44.8%→21.1%。
4. **若保留 68.2%→58.8%，不能只改正文或图注。**现有图片内部标题和纵轴均写 final-use，至少要重新导出一张数据不变但内部标签正确的 Figure 5。若要保留 final-use 含义，则必须换用 `*_terminal_*` 字段重画，并更新数字、正文和图注。
5. **最新版 DOCX 的两张核心表确实只有相关叙述和 Notes，没有表体。**Cox 表应恢复四个阶段，省级支持表应恢复四个 outcome。数字仍完整存在于 `result/tables/` 和 `manuscript.tex`，属于投稿文档呈现缺失，不是结果丢失。

## 2. Cox survival 样本与事件口径

### 2.1 当前脚本的实际筛选

证据文件：

- `data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv`
- `data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv`
- `code/coal_retirement_survival_final_0820.py`
- `result/tables/0820_coal_retirement_survival_final/period_specific_cox.csv`
- `result/tables/0820_coal_retirement_survival/segmented_cox.csv`

初始资格筛选保留：`asset == coal`；状态不属于 cancelled、construction、announced、shelved、permitted、pre-permit、mothballed；`start_year` 和 `capacity_mw` 可解析；省份存在 `coalexp_pre`；有退役年时，退役年可解析且不早于投产年。当前数据有 **4,326** 条记录通过该层筛选。

脚本随后把记录切入 2000—2011、2012—2015、2016—2020、2021—2025 四个日历阶段：

```text
interval_start = max(start_year, first_year)
interval_end   = min(retired_year or last_year + 1, last_year + 1)
drop if interval_end <= interval_start
event = 1 if first_year <= retired_year <= last_year
```

因此，eligible record 与形成正时长 Cox interval 的分析机组不是同一计数。

### 2.2 4,326 如何变成 4,323

4,326 条初始合格记录中，**4,323** 条至少形成一个正时长风险区间。三条未形成任何区间的记录为：

| GEM ID | 省份 | 投产年 | 退役年 | 容量 MW | 原因 |
|---|---|---:|---:|---:|---|
| G100000103207 | Guizhou | 1957 | 2000 | 100 | 首段 `interval_start=interval_end=2000` |
| G100000103208 | Guizhou | 1957 | 2000 | 100 | 同上 |
| G100000114127 | Shanxi | 1954 | 2000 | 186 | 同上 |

所以 4,323 对应 `episodes['unit_id'].nunique()`，即形成正时长风险区间的机组数；4,326 是上游合格记录数。两者无需人为对齐，但样本说明必须区分。

### 2.3 1,078 如何变成 952

初始合格记录中，2000—2025 年共有 **1,078** 个退役年份。最终区间构造排除的恰好是四个阶段起始年的退役：

| 阶段起始年 | 合格记录中的退役数 | 进入 Cox 的事件数 |
|---:|---:|---:|
| 2000 | 3 | 0 |
| 2012 | 30 | 0 |
| 2016 | 74 | 0 |
| 2021 | 19 | 0 |
| **合计** | **126** | **0** |

原因不是这些机组都在投产当年退役，而是年频数据与阶段切分的组合：在阶段第一年退役时，该阶段的 `interval_start` 和 `interval_end` 同为阶段首年，零时长区间被删除；事件也不会分给前一阶段。

```text
1,078 - (3 + 30 + 74 + 19) = 952
```

模型分项为：

| 阶段 | 正时长区间数 | 模型事件数 |
|---|---:|---:|
| 2000—2011 | 2,852 | 443 |
| 2012—2015 | 2,904 | 135 |
| 2016—2020 | 3,219 | 253 |
| 2021—2025 | 3,369 | 121 |
| **合计** | **12,344** | **952** |

区间数和事件数与较早的 `segmented_cox.csv` 完全一致，总数又与最终 `period_specific_cox.csv` 完全一致。12,344 是四阶段正时长风险区间之和，不是无法定位的旧稿数字。

### 2.4 来源判断和准确表述

当前仓库仅有一个提交，最终结果目录也缺少脚本声明应生成的 `run.log`，所以无法从版本历史核对当时的软件环境；但这不再阻止样本计数复核。当前数据、当前脚本、较早分段结果和最终结果在 4,323、952、12,344 上闭合。没有证据需要假定旧数据快照、旧筛选或手工排除。

真正待处理的是阶段边界事件的编码合理性。本阶段不重新估计，因此不判断纳入 126 个事件后 HR 如何变化，也不新增模型结论。

现有结果的准确口径是：

- **4,323 coal units contributing at least one positive-duration risk interval**；
- **952 modeled retirement events**；
- **12,344 unit-period risk intervals**。

不宜无修饰地写 “the current release identifies 4,323 coal units and 952 retirement events”，因为当前派生数据先识别出 4,326 条合格记录和 1,078 个 2000—2025 年退役年份；4,323/952 是风险区间构造后的分析口径。

## 3. Figure 5 panel (a) 指标定义

### 3.1 原始项目与两套字段

`code/build_energy_balance_panel.py` 从以下 Wind 导出读取省级能源平衡项目：

- `data/append_0518/数据模板命名1.csv`：煤、油品、液化石油气平衡表；
- `data/append_0518/数据模板 5.csv`：天然气、电力平衡表。

构造脚本明确把两个中文项目映射为不同后缀：

| 原始项目 | 脚本后缀 | 示例字段 |
|---|---|---|
| 能源消费 | `consumption` | `coal_consumption_10k_tce_approx` |
| 终端消费量 | `terminal` | `coal_terminal_10k_tce_approx` |

五类原始表和折标方式为：

| 类别 | 原始平衡表 | 原始单位 | 折为万吨标准煤的脚本系数 |
|---|---|---|---:|
| Coal | 煤平衡表 | 千吨 | 0.7143 / 10 |
| Oil products | 油品平衡表 | 千吨 | 1.4286 / 10 |
| LPG | 液化石油气平衡表 | 千吨 | 1.7143 / 10 |
| Natural gas | 天然气平衡表 | 百万立方米 | 0.133 |
| Electricity | 电力平衡表 | 百万千瓦时 | 0.01229 |

代码将这些系数定义为 approximate cross-energy aggregation，原始物理量仍为权威字段。仓库没有单独版本化的官方折标依据或五个系列可加总性的外部核验，因此名称应保留 constructed 和 approximate 限定。

### 3.2 Figure 5 的全国汇总算法

`plot_annual_composition_shares()` 实际读取：

```text
coal_consumption_10k_tce_approx
oil_consumption_10k_tce_approx
lpg_consumption_10k_tce_approx
gas_consumption_10k_tce_approx
electricity_consumption_10k_tce_approx
```

对 2006—2022 年，先逐类别按年份跨省求和，再用五类全国和的合计作分母。煤炭份额即：

```text
sum_provinces(coal_consumption_tce)
--------------------------------------------------------------- × 100
sum_provinces(coal + oil + LPG + gas + electricity consumption_tce)
```

这不是省级份额的简单平均。Pandas 求和跳过缺失值；2006 和 2022 两个端点的五类字段均有 30 个省级非缺失值，西藏没有这组能源平衡数据。

| 字段口径 | 2006 煤炭份额 | 2022 煤炭份额 | 含义 |
|---|---:|---:|---|
| `*_consumption_10k_tce_approx` | 68.2109% | 58.8413% | 五个“能源消费”系列的构造篮子 |
| `*_terminal_10k_tce_approx` | 44.8436% | 21.1224% | 五个“终端消费量”系列的构造篮子 |

68.2%→58.8% 与现图数据一致，但与 final-use 标签不一致。

### 3.3 回归别名与 Figure 5 的关系

`code/build_append_0518_full_panel.py` 的别名映射为：

| 别名 | 源字段 | 口径 |
|---|---|---|
| `energy5_int` | `energy5_terminal_10k_tce_per_gdp_approx` | 五类终端消费量折标合计 / GDP |
| `coalterm_int` | `coal_terminal_10k_tce_per_gdp_approx` | 煤炭终端消费量折标 / GDP |
| `coalshare5` | `coal_share_energy5_terminal_approx` | 煤炭终端消费量 / 五类终端消费量合计 |

因此，省级 FE 使用 `terminal`，Figure 5 panel (a) 使用 `consumption`。现图不是 `coalshare5` 的全国版，不能用来直接可视化或验证该回归变量。

### 3.4 68.2%→58.8% 的准确命名和处理选择

若保留现有数字，准确英文名称为：

> Coal's share of a constructed five-series energy-consumption basket, based on provincial energy-balance “energy consumption” items converted to approximate standard-coal equivalents.

简写可用：

> Coal share of the constructed five-energy consumption basket (%).

不能称为 five-energy final-use basket、final-energy composition、`coalshare5` 的全国汇总或 total primary energy share。

| 希望保留的含义 | 需要的处理 | 是否改变柱形数据 |
|---|---|---|
| 保留 68.2%→58.8% 的 `consumption` 序列 | 改正文、图注，并重新导出 panel (a) 内部标题和纵轴标签 | 否；数据不变，但图片须重新导出 |
| 保留 final-use 且与 `coalshare5` 一致 | 改用五个 `*_terminal_*` 字段重画，同步改端点数字、正文和图注 | 是 |

不能只改正文/图注而保留当前图片，因为 PNG/PDF 内嵌 “(a) Final-use energy composition” 和 “Share of five-energy final use (%)”。

### 3.5 命名沿革

- 0718 英文稿已有 `energy5_int`、`coalterm_int`、`coalshare5` 的 final-use/terminal 命名，但尚无 68.2%→58.8% 或当前 Figure 5。
- 0820 重构稿首次把 68.2%→58.8% 引入摘要、结果段、Figure 5 和图注，并从一开始称为 five-energy final-use basket。
- 0901 DOCX 继承了 0820 的文字和图片标签；仓库中没有更早、准确称为 `consumption` 的 Figure 5 版本。

这不是后期图注偶然改错，而是新增 Figure 5 时把省级 FE 的 `terminal` 命名沿用到了另一套 `consumption` 字段。

## 4. 最新 DOCX 缺失的两张核心结果表

### 4.1 缺失状态

最新文件为 `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`。对 `word/document.xml` 的完整表格结构核对显示：

- DOCX 共含 7 个 OOXML 表格对象；
- 只有 evidence-layer 表和 direct-asset summary 表是多行结果表；
- Figure 1—5 的 Notes 分别被保存为单单元格表格；
- Cox 表的四行数值不在任何表格单元格中；
- supporting provincial evidence 表的四行数值也不在任何表格单元格中；
- 两张表在正文中有结果叙述和 Notes，但没有可见结果表体。

`output/energy_policy_lockin_0820/manuscript.docx` 已有相同的 7 表结构和相同缺口。因此 0901 版本继承了 0820 的转换缺失，不是 0901 排版时新发生的结果删除。

### 4.2 Cox hazard-ratio table

`manuscript.tex` 中的拟定表题是 **Coal-unit retirement hazard by calendar period and pre-policy coal exposure**。

应恢复的行列为：

| Period | Hazard ratio | Clustered SE of log hazard | p value | Retirement events |
|---|---:|---:|---:|---:|
| 2000—2011 | 1.263 | 0.126 | 0.063 | 443 |
| 2012—2015 | 1.014 | 0.241 | 0.955 | 135 |
| 2016—2020 | 1.084 | 0.219 | 0.713 | 253 |
| 2021—2025 | 1.124 | 0.230 | 0.613 | 121 |

表注至少应保留现有拟定信息：left-truncated Cox；12,344 unit-period risk intervals；capacity 和 vintage controls；province-clustered standard errors；coal exposure 按省级标准差标准化；calendar-period associations/contrasts 为诊断性而非因果政策检验。

最可靠来源：

- **主结果源**：`result/tables/0820_coal_retirement_survival_final/period_specific_cox.csv` 中 `specification == standardized_continuous` 的四行。它直接包含 HR、log-hazard clustered SE、p、阶段事件数和 `n_intervals`。
- **区间计数交叉核对**：`result/tables/0820_coal_retirement_survival/segmented_cox.csv`。它可核对各阶段区间数和事件数，但较早 HR 规格不同，不能替代最终 HR。
- **排版定义**：`output/energy_policy_lockin_0820/manuscript.tex` 第 173—190 行提供拟定列名、舍入值和表注。

不得用 `median_high_coal` 四行替代主表；Figure 2 左图的 median split 是展示规格，拟定 Cox 主表是连续标准化暴露规格。

### 4.3 Provincial FE / supporting-results table

`manuscript.tex` 中的拟定表题是 **Supporting provincial evidence: operating and compositional adjustment**。

应恢复的行列为：

| Outcome | Baseline coefficient | p value | Pre-trend p value | Province-trend coefficient |
|---|---:|---:|---:|---:|
| Five-energy final intensity | -0.289 | 0.021 | 0.052 | -0.123 |
| Final-coal intensity | -0.426 | <0.001 | 0.041 | -0.057 |
| Five-energy coal share | -0.250 | 0.003 | 0.840 | 0.090 |
| Industrial SO2 | -72.589 | 0.001 | 0.053 | 28.616 |

这是跨规格诊断摘要，没有单一 CSV 同时保存全部五列。可靠来源应逐列指定：

| 表中字段 | 主结果来源 |
|---|---|
| Baseline coefficient、baseline p | `result/tables/0718_manuscript_revision/Table_0718_1_Baseline_CI_Windows.csv` |
| Pre-trend p value | `result/tables/0718_manuscript_revision/Table_0718_3_Event_Studies.csv` 的 `pretrend_p` |
| Province-trend coefficient | `result/tables/0718_manuscript_revision/Table_0718_5_Robustness.csv` 中 `specification == province_linear_trends` |
| 拟定行名、列名、舍入和 Notes | `output/energy_policy_lockin_0820/manuscript.tex` 第 198—215 行 |

`result/tables/0820_trend_robustness/Table_0820_Trend_Robustness.csv` 可作交叉核对：其 baseline 和 full-period province-linear-trend 结果与上述文件在报告精度内一致；但它还含多个截断窗口和其他趋势规格，不应在恢复当前四行表时未经说明地替换原拟定来源。

表注至少应保留：province and year fixed effects；province-clustered standard errors；outcome-specific coverage（2007—2022 或 2007—2023）；baseline coefficient 为 `Post-2012 × pre-policy coal exposure`；该表是 diagnostic summary 而非 causal policy-effect table。

这里的第二张缺表是上述 operating/compositional supporting table，不是另做一张 GEM province-year lifecycle regression 表。后者在正文中只有叙述，保存来源是 `result/tables/0721_gem_project_lifecycle/Table_0721_GEM_Project_Lifecycle.csv`；`manuscript.tex` 没有为它定义第三张待恢复表体。

## 5. 对 01 审计的更正与保留

### 5.1 需要更正

`01_evidence_chain_audit.md` 关于 Cox 的以下判断由本报告替代：

- “当前数据和代码得到 4,326 eligible units / 1,078 retirement events，因此不能复得 4,323/952”；
- “4,323/952 必然来自旧快照、旧筛选或不可定位版本”的推断方向。

准确判断是：

- 当前数据/代码的**初始资格层**为 4,326 / 1,078；
- 当前数据/代码的**正时长 Cox 风险区间层**为 4,323 / 952 / 12,344；
- 两层差异可由当前脚本确定地解释，无须假定数据版本变化。

### 5.2 仍然保留

- Cox 目录缺 `run.log`，环境和 `lifelines` 版本未锁定；
- 阶段边界年的 126 个退役事件被区间构造排除，需要在后续方法审查中决定是否为预期设计；本阶段不重新估计，不判断其对 HR 的影响；
- Figure 5 panel (a) 的 final-use 标签与 `consumption` 字段冲突；
- 最新 DOCX 缺 Cox 和省级支持结果两张表的表体。

## 6. 本阶段终审判断

| 问题 | 最终诊断 | 投稿前动作性质 |
|---|---|---|
| Cox 4,323 / 952 / 12,344 | 当前数据和代码可复得；此前是计数层级混淆 | 更正样本定义；另行审查 126 个边界年事件的编码 |
| Figure 5 68.2%→58.8% | 数字正确但属于 `consumption` 构造篮子，不是 final-use | 至少重导出标签正确的图片；若坚持 final-use，则换字段重画并更新数字 |
| Cox 结果表 | DOCX 表体缺失，结果 CSV 完整 | 从最终 continuous-exposure CSV 恢复四行五列 |
| Provincial supporting table | DOCX 表体缺失，需由三个结果 CSV 组合恢复 | 按 `manuscript.tex` 的四行五列恢复并保留诊断性表注 |

本报告只诊断证据和口径，不修改论文、代码、数据或已有结果，不重估模型，也不对边界事件重新编码后的结果作任何推测。