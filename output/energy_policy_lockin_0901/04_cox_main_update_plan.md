# Boundary-inclusive Cox 主结果：论文更新计划

日期：2026-09-07  
对象：`output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`  
用途：列出下一阶段必须执行的 Cox 数值、方法说明、Figure 2 和表注更新。本文件不修改 DOCX，也不进行一般语言润色。

## 1. 已确定的新主结果口径

主规格：

- retirement event time = `reported retired_year + 1`；
- event period 仍按原始 reported retirement year 归入 2000–2011、2012–2015、2016–2020、2021–2025；
- 4,326 contributing coal units；
- 1,078 modeled retirement events；
- 12,470 unit-period risk intervals；
- `lifelines 0.30.0`、`CoxPHFitter`；
- standardized continuous pre-policy provincial coal exposure；
- capacity 和 vintage controls；
- province-clustered robust standard errors；
- left truncation 保持不变。

论文 Cox 主表应采用：

| Period | HR | Clustered SE of log hazard | p value | 95% CI | Retirement events |
|---|---:|---:|---:|---:|---:|
| 2000–2011 | 1.299 | 0.124 | 0.035 | [1.019, 1.657] | 446 |
| 2012–2015 | 1.117 | 0.181 | 0.542 | [0.783, 1.594] | 165 |
| 2016–2020 | 1.127 | 0.212 | 0.573 | [0.744, 1.708] | 327 |
| 2021–2025 | 1.110 | 0.212 | 0.622 | [0.733, 1.681] | 140 |

权威资产：

- `result/tables/0907_cox_boundary_main/Table_Cox_Main_Boundary_Inclusive.csv`；
- `result/tables/0907_cox_boundary_main/Table_Cox_Main_Boundary_Inclusive_metadata.json`；
- `result/figures/0907_cox_boundary_main/Figure_2_retirement_evidence_boundary_inclusive.png`；
- `result/figures/0907_cox_boundary_main/Figure_2_retirement_evidence_boundary_inclusive.pdf`。

表和图的数据源是 `result/tables/0907_cox_boundary_sensitivity/cox_boundary_primary_comparison.csv` 中 `specification == end_of_reported_year` 的四行，没有硬编码估计结果。

## 2. 必须替换旧样本数字的段落

以下以最新版 DOCX 的章节和段落开头作为定位锚点；实际修改时不要依赖 OOXML 临时序号。

### 2.1 Introduction / evidence overview

定位：以 **“The analysis combines three forms of evidence.”** 开头的段落。

当前内容包含：

> retirement histories for 4,323 coal units

必须更新为 4,326 contributing coal units。若该句同时描述事件覆盖，应使用 1,078 modeled retirement events。不要继续把 4,323 写成当前主分析的机组数。

### 2.2 Methods / asset data

定位：以 **“The asset data are reconstructed from the January 2026 Global Coal Plant Tracker...”** 开头的段落。

当前内容包含：

> The current release identifies 4,323 coal units entering the retirement analysis and 952 retirements.

必须更新：

- 4,323 → **4,326 contributing units**；
- 952 → **1,078 modeled retirement events**；
- 明确这些事件是 reported retirement years 落在 2000–2025 的 eligible events；
- 避免把 `retired_year + 1` 描述成观测到的精确退役日期。

### 2.3 Methods / survival model

定位：以 **“The asset analysis has two parts.”** 开头的段落。

在现有四阶段、capacity/vintage controls、province clustering 和 exposure interaction 描述之后，必须补入时间约定：

- GEM 只报告 calendar year，没有精确月日；
- 主规格把机组视为在 reported retirement year 内仍处于风险，并把连续事件时点设在该报告年末，即 `retired_year + 1`；
- 事件的政策阶段标签仍由原始 reported retirement year 决定；
- left truncation 继续按机组投产年与阶段起点计算。

定位：以 **“Compared with a province-year retirement share...”** 开头的限制段落。

应在限制中说明年末时点是 annual-time convention，而不是精确日期。不要把这一方法选择写成数据精度的提高。

### 2.4 Cox table notes

定位：以 **“Notes: Left-truncated Cox model with 12,344 unit-period observations...”** 开头的段落。

必须替换并补齐：

- 12,344 → **12,470 unit-period risk intervals**；
- 加入 **4,326 contributing units**；
- 加入 **1,078 modeled retirement events**；
- 明确 `lifelines 0.30.0 / CoxPHFitter`；
- 保留 capacity and vintage controls；
- 保留 province-clustered robust standard errors；
- 保留 exposure 按省级 pre-policy 分布标准化、HR 对应 1 SD；
- 加入 end-of-reported-year annual-time convention；
- 加入 event period 按 reported retirement year 分配；
- 保留 observational / diagnostic、非因果政策检验的限定。

## 3. Abstract 必须更新的内容

定位：Abstract 中：

> The survival specifications show no statistically detectable acceleration of coal-unit retirement in high-coal-exposure provinces.

Abstract 当前没有 4,323/952/12,344，也没有旧 HR，因此不需要加入新的样本数字。需要更新的是推断口径：

- 可以概括三个 post-2012 period-specific HR 均未显著偏离 1，且 95% CI 均跨 1；
- 不得把 `p > 0.05` 写成已正式接受 post 与 pre 系数相等；
- 不得写成正式的 post-versus-pre equality test 已经通过；
- 不需要在 Abstract 强调 pre-2012 p=0.035，除非正文研究问题要求突出这一点。

## 4. Results 必须更新的内容

### 4.1 Results subsection heading

定位：标题 **“High coal exposure did not show a detectable post-2012 retirement acceleration”**。

标题只有在正文立即把 “detectable” 限定为 post-period HR 的 CI 包含 1 时才可保留。标题不能被解释为已经完成并接受 post-versus-pre equality test。

### 4.2 Cox 数值段落

定位：以 **“The retirement analysis does not show faster exit in coal-intensive provinces after 2012.”** 开头的段落。

必须替换四个旧 HR：

- 1.26 → **1.30**（精确表值 1.299）；
- 1.01 → **1.12**（精确表值 1.117）；
- 1.08 → **1.13**（精确表值 1.127）；
- 1.12 → **1.11**（精确表值 1.110）。

若正文括号内报告 p 值和 CI，应同步使用新值：

- 2000–2011：p=0.035，95% CI [1.019, 1.657]；
- 2012–2015：p=0.542，95% CI [0.783, 1.594]；
- 2016–2020：p=0.573，95% CI [0.744, 1.708]；
- 2021–2025：p=0.622，95% CI [0.733, 1.681]。

该段可以陈述三个 post-2012 CI 均跨 1。不得把“不显著”升级为“证明没有加速”或“post 与 pre 相等”。

### 4.3 Figure 2 解释段落

定位：以 **“Figure 2 presents the result in two forms.”** 开头的段落。

需要保持：

- panel (a) 是 2012 年初 operating cohort 的未调整 KM 展示；
- cohort 总数仍为 2,409，高煤暴露 1,390、低煤暴露 1,019；
- panel (b) 是控制 capacity 和 vintage 后的四阶段 Cox estimates；
- 三个 post-2012 CI 均包括 1；
- 图是 observational display。

需要新增或明确：KM 使用与主 Cox 相同的 end-of-reported-year convention。30 个 reported-2012 retirement events 现在位于 years-since-2012 = 1，而不是 time 0。

### 4.4 其他重复结论段落

以下段落不含旧样本数字，但对 “acceleration” 有重复表述，应同步检查推断口径：

- Introduction 中以 **“The three margins moved at different speeds.”** 开头的段落；
- Results/Discussion 中以 **“The national stock trajectory might also be driven...”** 开头的段落；
- Conclusion 中以 **“Operating and compositional indicators alone cannot assess China’s transition.”** 开头的段落。

这些位置可以继续说“未检测到 post-2012 differential retirement acceleration”，但必须与主结果的实际检验对象一致：三个 post-period exposure HR 未显著偏离 1。不要暗示已正式检验 post HR 与 pre HR 相等。

## 5. Figure 2 notes 必须更新的内容

定位：以 **“Notes: Panel (a) is an unadjusted Kaplan–Meier display for the 2,409 coal units...”** 开头的段落。

保留：

- 2,409-unit 2012 operating cohort；
- high/low exposure 按省级 pre-policy exposure 中位数划分；
- panel (b) 的 HR 是每 1 provincial SD；
- capacity/vintage controls；
- 95% CI 使用 province-clustered robust SE；
- observational、非政策因果效应。

新增：

- 两个 panel 均使用 end-of-reported-year annual-time convention；
- reported year R 的退役时点编码为 R+1；
- Cox event period 仍按 reported retirement year R 分配；
- 2012 年退役不会被编码为 time 0。

嵌入新资产：

`result/figures/0907_cox_boundary_main/Figure_2_retirement_evidence_boundary_inclusive.png`

不要覆盖或重新链接到 `result/figures/energy_policy_lockin_0820/Figure_2_retirement_evidence.*`。

## 6. 主文中必须消失的旧数值

从主文叙述、主 Cox 表、Figure 2 panel (b) 及其 notes 中删除或替换：

- **4,323** contributing units；
- **952** modeled retirement events；
- **12,344** unit-period observations/intervals；
- 阶段事件数 **443、135、253、121**；
- 主结果 HR **1.263/1.26、1.014/1.01、1.084/1.08、1.124/1.12**；
- 旧 HR CI **[0.987, 1.616]、[0.632, 1.627]、[0.706, 1.664]、[0.715, 1.765]**；
- 与旧 HR 对应的 p 值 **0.063、0.955、0.713、0.613**。

注意：数字 1.12 可能在其他非 Cox 语境出现，替换时必须按段落和结果来源定位，不能全局机械替换。

主文新阶段事件数应为 **446、165、327、140**，合计 1,078。

## 7. 旧 952-event 版本在 robustness / supplement 中的保留方式

旧结果可以保留，但必须与新主规格清楚分层：

1. 标题或规格名使用 **legacy start-of-reported-year coding** 或 **boundary-event-excluding legacy specification**；不要继续称为 baseline/main specification。
2. 明确其连续事件时点为 `retired_year`，阶段首年事件形成零时长 interval 并被删除。
3. 明确被排除事件：2000 年 3 个、2012 年 30 个、2016 年 74 个、2021 年 19 个，合计 126 个。
4. 报告旧样本口径：4,323 positive-duration contributing units、952 modeled events、12,344 intervals。
5. 可保留旧四期 HR、SE、p 和 CI，用于说明方向与数量级对时间编码的稳健性。
6. supplement 应与 boundary-inclusive 主结果并列展示，不能把两组样本计数或事件数混写在同一规格行。
7. robustness 结论限于：方向未反转、数量级相近、三个 post-period HR 在两种编码下均未显著偏离 1。
8. 不得利用旧版或新版哪个更显著来决定主规格；主规格选择依据是 annual-time 含义一致和完整保留 observed retirement-year events。

建议 robustness 数据源：

- 旧结果：`result/tables/0820_coal_retirement_survival_final/period_specific_cox.csv` 中 `standardized_continuous`；
- 并列对照：`result/tables/0907_cox_boundary_sensitivity/cox_boundary_primary_comparison.csv`；
- 方法审计：`output/energy_policy_lockin_0901/03_cox_boundary_sensitivity_audit.md`。

## 8. 明确禁止的推断

三个 post-2012 p 值大于 0.05，只支持“各期 exposure HR 未被统计区分于 1”。它们不等于：

- post HR 与 pre HR 已被证明相等；
- 已接受无加速的原假设；
- 政策没有影响退役；
- 高煤暴露地区与低煤暴露地区的退役过程完全相同。

若论文需要正式声称 post-versus-pre coefficient equality，必须另行进行与主模型、省级聚类稳健协方差一致的跨期 contrast。本阶段没有进行该检验。0820 的 `period_difference_tests.csv` 是 model-based、非 cluster-robust diagnostic，不能作为正式 equality test。

## 9. 本阶段不处理的内容

- 不修改最新版 DOCX；
- 不修改三个原始 survival 脚本；
- 不修改 GEM 数据或 0820 原始结果；
- 不覆盖旧 Figure 2 或旧 Cox 表；
- 不修改 Figure 5；
- 不进行与 Cox 数值和方法口径无关的语言润色。
