# Figure 5 panel (a) 变量口径选择审计

审计日期：2026-09-07  
范围：只读复核原绘图脚本和论文相关文字；新建两套候选图、核对 CSV 和 metadata。未修改论文 DOCX、原始数据、原始绘图脚本、旧 Figure 5 或 Cox 资产。

## A. 当前问题事实

### A.1 现有 Figure 5 panel (a) 的实际计算

`code/plot_energy_policy_evidence_figures_0822.py` 的 `plot_annual_composition_shares()` 实际使用以下五个字段：

- `coal_consumption_10k_tce_approx`
- `oil_consumption_10k_tce_approx`
- `lpg_consumption_10k_tce_approx`
- `gas_consumption_10k_tce_approx`
- `electricity_consumption_10k_tce_approx`

年份范围为 2006–2022。对每一年和每一能源类别，脚本先跨省求和，再用五类全国和的加总作分母：

`national component sum / sum of five national component sums × 100`。

这不是省级份额的简单平均。`groupby.sum()` 按 Pandas 默认跳过缺失值。本次逐年复核显示，不论使用 `consumption` 还是 `terminal` 字段，2006–2022 的每一年、每一个能源字段都有 30 个非缺失省份。因此，两套结果的差异来自能源平衡项目口径，不是缺失值或省份覆盖变化。

Panels (b) 和 (c) 均使用 2006–2023 年，分别先对全国各省的 thermal/total capacity 和 thermal/total generation 求和，再计算份额。两个候选版均按原逻辑重新计算，没有改变它们的口径。

### A.2 变量名称冲突

现图的 68.2109%→58.8413% 是五个“能源消费”`*_consumption_*` 系列组成的构造篮子，但图内标题、纵轴、Abstract、Results 和 Figure 5 notes 将其命名为 final use。

省级 FE 的核心变量则明确使用 `terminal` 字段：

| FE 别名 | 底层口径 |
|---|---|
| `energy5_int` | `energy5_terminal_10k_tce_per_gdp_approx` |
| `coalterm_int` | `coal_terminal_10k_tce_per_gdp_approx` |
| `coalshare5` | `coal_share_energy5_terminal_approx` |

因此，现 Figure 5 panel (a) 不是 `coalshare5` 的全国汇总版。两者还存在汇总层级差异：FE 使用省年份额，Figure 5 使用全国分子、分母先求和后得到的份额。terminal 版能统一底层字段口径，但不应说成与 FE 估计量完全相同。

## B. Terminal/final-use candidate

### B.1 新数字

| 类别 | 2006 | 2022 | 变化（百分点） |
|---|---:|---:|---:|
| Coal | 44.8436% | 21.1224% | -23.7212 |
| Oil products | 28.5778% | 29.0444% | +0.4666 |
| LPG | 2.3156% | 2.6659% | +0.3503 |
| Natural gas | 3.8553% | 11.5099% | +7.6546 |
| Electricity | 20.4076% | 35.6573% | +15.2497 |

核心端点表述应为：煤炭占构造的五能源 final-use/terminal-use 篮子的份额从 2006 年的 **44.8%** 降至 2022 年的 **21.1%**。该篮子是 approximate cross-energy aggregation，不是 total primary energy，也不应在没有限定词时称为完整的全社会 final energy。

### B.2 资产路径

- `result/figures/0907_figure5_terminal/Figure_5_annual_composition_shares_terminal.png`
- `result/figures/0907_figure5_terminal/Figure_5_annual_composition_shares_terminal.pdf`
- `result/tables/0907_figure5_terminal/Figure_5_panel_a_terminal_audit.csv`
- `result/tables/0907_figure5_terminal/Figure_5_panels_bc_audit.csv`
- `result/tables/0907_figure5_terminal/Figure_5_terminal_metadata.json`

### B.3 优缺点

**优点**

- 与 `energy5_int`、`coalterm_int` 和 `coalshare5` 的底层 `terminal` 字段一致，可作为相同构造篮子的全国描述。
- 与论文现有 final-use 概念一致，不需要在同一证据链中引入另一个未用于 FE 的 consumption 篮子。
- 对审稿人而言，图、文字和支持回归的变量谱系更容易核对。

**缺点及需要处理的问题**

- 煤炭端点从 68.2%→58.8% 改为 44.8%→21.1%，降幅由约 9.4 个百分点变为约 23.7 个百分点，Abstract、结果概览、Figure 5 解读段和图注都必须更新。
- 电力和天然气份额的端点也明显改变；如正文新增或报告这些数字，必须使用 terminal 版数值。
- 数值变化大不等于应否选用该版本的方法理由。选择应取决于变量定义和证据链，而不是降幅更大。

这些更改是“端点数字和变量说明的实质替换”，但不要求改写论文的核心定性结论：煤炭份额下降、电力和天然气份额上升、份额变化不等于煤电资产退役，这些方向均保持不变。

## C. Consumption-relabel candidate

### C.1 数字

| 类别 | 2006 | 2022 | 变化（百分点） |
|---|---:|---:|---:|
| Coal | 68.2109% | 58.8413% | -9.3696 |
| Oil products | 16.5562% | 14.5326% | -2.0235 |
| LPG | 1.2367% | 1.5748% | +0.3380 |
| Natural gas | 2.5508% | 7.3689% | +4.8182 |
| Electricity | 11.4454% | 17.6824% | +6.2370 |

该版保留现有数据和 68.2%→58.8% 端点，但将 panel (a) 图内标题和纵轴改为 **constructed five-energy consumption basket**，不再使用 final-use。

### C.2 资产路径

- `result/figures/0907_figure5_consumption_relabel/Figure_5_annual_composition_shares_consumption_relabel.png`
- `result/figures/0907_figure5_consumption_relabel/Figure_5_annual_composition_shares_consumption_relabel.pdf`
- `result/tables/0907_figure5_consumption_relabel/Figure_5_panel_a_consumption_audit.csv`
- `result/tables/0907_figure5_consumption_relabel/Figure_5_panels_bc_audit.csv`
- `result/tables/0907_figure5_consumption_relabel/Figure_5_consumption_metadata.json`

### C.3 优缺点

**优点**

- 保留现有柱形数据和 68.2%→58.8%，不需要替换端点数值。
- 修正后的图内标题和纵轴与底层 `consumption` 字段如实对应。

**缺点**

- 必须把 Abstract、Results 和 Figure 5 notes 中与 68.2%→58.8% 相连的 final-use 表述全部替换为 constructed five-energy consumption basket。因此，虽然数字改动小，概念标签的改动并不小。
- 省级 FE 仍使用 `terminal`。论文必须额外说明，Figure 5 panel (a) 是一个与 FE 不同的全国描述口径，不是 `coalshare5` 的全国对应物。
- 如果 Figure 5 继续被介绍为对省级 final-use 结果的 national composition check，审稿人可能质疑为何描述图和回归使用不同的能源平衡项目。只有将其清楚界定为独立的 consumption-basket 描述才可以防止这种误读。

## D. 投稿选择与明确推荐

| 判断维度 | Terminal/final-use version | Consumption-relabel version |
|---|---|---|
| 与省级 FE 变量定义的一致性 | **高**：使用相同 `terminal` 字段谱系 | **低**：使用 FE 未使用的 `consumption` 字段 |
| Abstract/Results 数字改动 | 较大：端点改为 44.8%→21.1% | 较小：保留 68.2%→58.8% |
| Abstract/Results 概念改动 | 较小：现有 final-use 主线可保留，但必须加 constructed/approximate 限定 | 较大：必须改为 consumption basket，并与 FE 口径分开 |
| 审稿风险 | **较低**：证据链口径更统一 | 较高：需解释图与 FE 为何不同 |
| 是否因数值“更好看”而选择 | 不应；仅以定义一致性为理由 | 不应；也不应仅为保留旧数字而选择 |

**推荐将 terminal/final-use version 作为新的 Figure 5。**

理由是它与正文省级 FE 的核心变量定义一致，并使 Figure 5 作为 national composition check 时有清晰、可追溯的变量关系。这一推荐与煤炭降幅是否更大无关。consumption-relabel 版在把它明确定义为独立的全国描述指标时仍是方法上可用的备选，但它不应继续被用来支撑或图解 `coalshare5`。

## E. 采用推荐的 terminal 版后必须改动的论文句子

以 `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx` 为定位对象。本节只指定实质性数字和口径替换，不进行语言润色。

### E.1 Abstract

必须替换如下句子中的篮子限定和两个端点：

> The national composition also changed: coal’s share of the five-energy final-use basket fell from 68.2% in 2006 to 58.8% in 2022, while thermal capacity and generation shares declined.

实质更新为：**constructed five-energy final-use basket**；**44.8% in 2006**；**21.1% in 2022**。Abstract 中关于省级煤暴露与 five-energy final-use share 的 FE 句子本来就对应 terminal 口径，不应改成 consumption。

### E.2 Results

结果概览段中的以下句子必须更新：

> Nationally, coal’s share of the observed five-energy final-use basket fell from 68.2% in 2006 to 58.8% in 2022, while thermal capacity and generation shares also declined.

将 `observed five-energy final-use basket` 统一为 **constructed five-energy final-use basket**，并将端点替换为 **44.8%** 和 **21.1%**。

Figure 5 解读段中的以下句子必须更新：

> In the observed five-energy final-use basket, coal’s share declined from 68.2% in 2006 to 58.8% in 2022, while electricity and natural-gas shares increased.

将其口径替换为 **constructed five-energy final-use basket**，端点替换为 **44.8%** 和 **21.1%**。“electricity and natural-gas shares increased”的方向在 terminal 数据中仍然成立；如报告精确数字，应使用本报告 B.1 的 terminal 端点。

该段后续的两个限定仍必须保留：电力不是清洁能源类别的同义词；份额不识别存量煤电机组的退役。

### E.3 Figure 5 panel (a) 和 notes

提交稿中应使用新 terminal 图。新图内标题为 `Constructed five-energy final-use composition`，纵轴为 `Share of constructed five-energy final use (%)`。

现有 notes 中的以下句子必须替换：

> Panel (a) uses the five-energy final-use basket: coal, oil products, LPG, natural gas, and electricity.

新 notes 至少需明确：

- panel (a) 使用 coal、oil products、LPG、natural gas 和 electricity 的 **terminal-consumption fields**；
- 五类数值是跨能源折标后的 **constructed and approximate five-energy final-use basket**；
- 先跨省求年度和，再计算全国份额；
- 它不是 total primary energy，电力也不能被解读为清洁能源类别。

Panels (b) 和 (c) 的口径、端点和原 notes 不需因本次 panel (a) 修正而改变。

## F. 必须从新主稿中删除的旧数字和旧标签

如采用推荐的 terminal 版，以下内容不得继续作为 Figure 5 panel (a) 的主稿表述：

- **68.2% in 2006** 和 **58.8% in 2022**；
- 将这两个数字称为 `five-energy final-use basket`、`final-use energy composition` 或 `final-energy composition`；
- 旧 Figure 5 图像中基于 `consumption` 数据却标为 `(a) Final-use energy composition` 和 `Share of five-energy final use (%)` 的组合；
- 任何把 68.2%→58.8% 称为 `coalshare5` 的全国汇总、total primary energy share 或 terminal/final-use share 的文字；
- 任何把 44.8%→21.1% 无限定地扩展为完整的 total final energy 份额的表述。

旧 Figure 5 文件可在项目中保留作为历史资产，但不应在新主稿中继续引用。

## 终审结论

terminal 版和 consumption-relabel 版都能修复“图内标签与底层字段不一致”的直接错误，但只有 terminal 版同时统一了 Figure 5 与省级 FE 的变量谱系。因此，新主稿应采用 terminal/final-use candidate，同时对其构造性、近似折标和非 total-primary-energy 属性作出明确限定。
