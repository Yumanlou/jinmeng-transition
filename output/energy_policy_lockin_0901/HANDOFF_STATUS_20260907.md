# Energy Policy 投稿终审交接状态

状态日期：2026-09-07  
项目路径：`D:\大学\大三下\论文\投稿准备\jinmeng-transition`

## A. 当前工作目标

本项目正在进行 Energy Policy 投稿前终审。最终目标是对英文稿件进行完整的语言、AI 痕迹、逻辑、引用、数据来源、图表、投稿格式和可复现性检查，并在证据口径锁定后再正式修改主论文。

当前审计对象是：

`output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`

截至本交接文件生成时，该 DOCX **尚未根据 03–05 阶段的锁定结论修改**。

## B. 已完成阶段

### B.1 第一阶段 证据链审计

**文件**：`output/energy_policy_lockin_0901/01_evidence_chain_audit.md`

**目的**：对论文主张、Figure 1–5、Cox、省级 FE、资源依赖、可再生能源消纳、可靠性、政策文本和复现链进行全景核对。

**主要结论**：

- GEM 项目生命周期数字、省级 FE 主要结果和图表大部分可从库内数据与代码追溯。
- 省级强度结果对 pre-trend 和省线性趋势敏感，不得提升为绿色信贷的因果效果。
- Figure 3 实际只显示煤电 stock、renewable consumption 和 resource dependence 三个维度，不是全部 constraint bundle。
- Wind 外部接口、平台特定解析工具、Stata/Python 环境和运行日志使项目仅能部分复现。

**已锁定**：主证据链文件位置、Figure 3 的实际信息边界、省级 FE 的诊断性而非因果性、现有复现基础设施不完整。

**后续处理**：01 中对 Cox 4,323/952 的初步“版本冲突”判断已被 02 的精确计数更正，后续不应单独引用 01 的该项旧判断。主 DOCX 尚未更新。

### B.2 第二阶段 高优先级证据冲突诊断

**文件**：`output/energy_policy_lockin_0901/02_high_priority_evidence_diagnosis.md`

**目的**：精确追溯 Cox 样本数字、Figure 5 panel (a) 字段口径，并确认最新 DOCX 缺失的两张结果表。

**主要结论**：

- 4,326 条初始 eligible unit 中，4,323 条在旧规格下形成正时长风险区间。
- eligible records 中有 1,078 个 2000–2025 reported retirement year；旧区间编码机械排除四个阶段首年的 126 个事件，故旧 Cox 报告 952 个 modeled events。
- 126 个边界年退役为：2000 年 3 个、2012 年 30 个、2016 年 74 个、2021 年 19 个。
- Figure 5 panel (a) 的 68.2109%→58.8413% 使用 `*_consumption_10k_tce_approx`，不是 `*_terminal_*`。
- 最新 DOCX 缺 Cox hazard-ratio table 和 provincial FE/supporting-results table 的表体，但结果文件存在。

**已锁定**：上述计数关系、Figure 5 的 consumption/terminal 口径区别、DOCX 两张核心表缺失。

**后续处理**：Cox 边界编码已由 03–04 解决；Figure 5 已由 05 做出推荐；两张表和更新数字尚未插入 DOCX。

### B.3 第三阶段 Cox 边界事件敏感性

**文件**：`output/energy_policy_lockin_0901/03_cox_boundary_sensitivity_audit.md`

**目的**：判断 annual retirement-year 编码为何排除阶段首年事件，并在不改变估计器和主规格的前提下进行 boundary-inclusive 敏感性检验。

**主要结论**：

- `start_year` 和 `retired_year` 只有年，没有月日。
- 旧脚本令阶段起点与边界年退役的终点相同，再删除零时长区间；这是编码副作用，不是已文档化的方法设计。
- 推荐主规格将退役时间编码为 `retired_year + 1`，但 event period 仍按原 reported retirement year 归类。
- 纳入 126 个边界事件后，四阶段 HR 的方向和数量级没有实质反转；“no statistically detectable post-2012 retirement acceleration”仍受支持。

**已锁定**：boundary-inclusive end-of-reported-year specification 作为新主规格；旧 952-event 版本降为 legacy/robustness。

**后续处理**：在 Methods 中加入 annual-time convention，在 supplement/robustness 中保留旧规格，主稿不得把 post-2012 各期 `p > 0.05` 写成正式 post-versus-pre equality test。

### B.4 第四阶段 Cox 新主图表资产

**文件**：`output/energy_policy_lockin_0901/04_cox_main_update_plan.md`

**目的**：使用已锁定的 boundary-inclusive 结果新建 Figure 2 和 Cox 主表，并列出论文需替换的旧口径。

**主要结论**：

- 新主口径为 **4,326 contributing units / 1,078 modeled retirement events / 12,470 unit-period intervals**。
- 四期 HR 为：
  - 2000–2011: 1.299，95% CI [1.019, 1.657]；
  - 2012–2015: 1.117，95% CI [0.783, 1.594]；
  - 2016–2020: 1.127，95% CI [0.744, 1.708]；
  - 2021–2025: 1.110，95% CI [0.733, 1.681]。
- 新 Figure 2 panel (a) 使用与新 Cox 相同的年度时间约定；2012 年事件不再被编码为 time 0 而丢失。

**已锁定**：新 Figure 2、新 Cox 主表及 metadata 是主稿更新时的权威资产。

**后续处理**：尚未插入 DOCX；Abstract、Methods、Results、Figure 2 notes 和 Cox table notes 仍含旧数字或旧规格。

### B.5 第五阶段 Figure 5 变量口径选择

**文件**：`output/energy_policy_lockin_0901/05_figure5_variable_choice_audit.md`

**目的**：生成 terminal/final-use 和 consumption-relabel 两个候选 Figure 5，并根据与省级 FE 的变量一致性做投稿选择。

**主要结论**：

- 原 68.2109%→58.8413% 是 constructed five-energy **consumption** basket，不得继续称为 final use。
- 按相同全国汇总法使用五个 `*_terminal_10k_tce_approx` 字段时，煤炭份额为 **44.8436%→21.1224%**。
- 两套口径在 2006–2022 年每年、每字段均有 30 个非缺失省份；差异不是缺失覆盖造成。
- 推荐 terminal/final-use 版，因为它与 `energy5_int`、`coalterm_int`、`coalshare5` 的底层字段一致。推荐不是因为降幅更大。

**已锁定**：新主稿应使用 terminal/final-use candidate；需保留 `constructed`、`approximate` 和非 total-primary-energy 限定。

**后续处理**：新 Figure 5 尚未插入 DOCX；Abstract、Results 和 Figure 5 notes 仍有 68.2%→58.8% 及错误 final-use 标签。

## C. 当前第六阶段进度

第六阶段目标是 data/citation/reference audit。已开始检查数据来源、政策文本、government work reports、policy-language 结果、author-year citations 和参考文献。

**当前文件状态**：

- `output/energy_policy_lockin_0901/06_data_citation_reference_audit.md` **不存在**。
- 第六阶段没有已写入的半成品报告；已做工作仅存在于当时的只读检查输出和本交接摘要。

### C.1 已执行的只读检查

1. 使用 Python `zipfile` 和 `xml.etree.ElementTree` 读取 `Designed_for_Adjustment_2026-09-01.docx` 的 `word/document.xml`，提取全部段落、Methods、Results、Data availability 和参考文献列表；未修改 DOCX。
2. 读取 01–05 审计、`literature_map_50.md`、`local_refs.bib` 和 `submission_notes.md`的相关内容。
3. 用 `rg --files` 和 `rg -n` 检索 GEM、Wind、NEA、monthly generation、resource dependence、policy text、project pipeline 和核心 FE 变量的文件—脚本关系。
4. 读取 `build_energy_balance_panel.py`、`build_append_0518_full_panel.py`、`build_monthly_generation_stability_0718.py`、`build_nea_renewable_consumption_panel_0718.py`、`build_nea_coal_reliability_panel_0718.py`、`build_national_provincial_policy_attention_0721.py` 的关键输入、输出与口径。
5. 只读计算/核对了部分覆盖：能源平衡原始整理表 1995–2022，论文五能源组合 2006–2022；NEA renewable consumption 2015–2023；coal reliability 2018–2023；monthly generation 各技术的覆盖并不相同。
6. 提取正文所有含年份的 author-year citation groups；初步比对显示，DOCX 正文中已出现的 34 组/条参考来源都能在当前 reference list 找到，reference list 也未发现明显的正文未引条目；未发现需要 a/b 区分的同作者同年组合。这是初步结果，需在 06 中重新做可保留的系统对照。
7. 检查了晋蒙 policy-language 链：正文称“government-work-report text”，但 01 审计所指的晋蒙结果实际使用 `data/policy_texts/*_policy_documents_2000_2023.csv`、`build_policy_text_indices.py` 和 `policy_eval_0518_full_chain.do`；库内另有 Li (2025) PLOS ONE 的 31 省 2003–2023 government-work-report corpus 及独立脚本。两条链需在 06 中明确分开。
8. 定向查找了部分一手政策页面，包括 2012 Green Credit Guidelines、2013 Air Pollution Action Plan、2015 power-sector reform、2019 renewable consumption guarantee mechanism、2021 coal-unit upgrading plan、2021 carbon-peaking documents、2022 modern energy-system plan 和 2023 coal capacity-pricing mechanism。这些网页尚未整理进 06 报告。
9. 检查了 GEM 当前引用线索：库内 metadata 指向 Zenodo record `10.5281/zenodo.20843067`、CC BY 4.0；网页核对显示该 Zenodo record 的创建者/标题是 Modelblocks archive，其中收录 GEM releases，与 DOCX 中直接将该网址写为 Global Energy Monitor 作者的单一条目不完全对应。需在 06 中决定是分别引用 GEM 官方 tracker release 与 archive DOI，还是更正当前条目。

### C.2 只处于中途状态或未完成的检查

- 尚未完成用户要求的逐变量 A–H 数据来源矩阵。
- 基础面板 `data/final_data.1.3.4_did.csv` 中 GDP、population、secondary-industry share、urbanization、environmental expenditure 和 marketization index 的一手来源尚未从库内文档确认；不得自行猜测。
- 尚未完成全部 DOI/题名/期刊/年份的可保留核对表。
- 尚未把政策一手文件与论文每一个政策性句子逐项对齐。
- 尚未根据 `literature_map_50.md` 形成最终的“必要/高价值补充文献”短清单。
- 最后一条用于查找 TeX `addbibresource` 和仓库全部 `.bib` 的只读命令在用户中断时被终止，**没有产生可依赖的结果**。新接手者应重新执行，确认 `local_refs.bib` 是否只是增量文库，以及完整 BibTeX 源在哪里。

## D. 已锁定的关键决策

1. Cox 新主规格采用 **boundary-inclusive end-of-reported-year specification**：`retirement event time = retired_year + 1`，event period 仍按 reported retirement year 归类。
2. 旧 **4,323 / 952 / 12,344** 版本降为 **legacy/robustness specification**，不再作为主结果。
3. 新 Cox 主口径是 **4,326 units / 1,078 modeled retirement events / 12,470 unit-period intervals**。
4. Boundary-inclusive 新 Figure 2 已生成，但尚未插入 DOCX。
5. Figure 5 推荐采用 **terminal/final-use version**。
6. 原 **68.2%→58.8%** 属于 constructed five-energy **consumption basket**，不得再称为 final use。
7. Terminal/final-use version 的煤炭份额为 **44.8436%→21.1224%**（主文可四舍五入为 44.8%→21.1%）。
8. 最新 DOCX 仍未修改；正式改稿时需统一更新 Abstract、Methods、Results、Figure notes、Cox table notes、Data availability 和相关数字。
9. Post-2012 各期 Cox `p > 0.05` 不是 post-versus-pre 系数相等的正式检验，不得如此表述。
10. Figure 3 是三维描述性 typology，不是全部 constraints 的图示或机制检验。

## E. 新生成资产清单

### E.1 审计与交接 Markdown

- `output/energy_policy_lockin_0901/01_evidence_chain_audit.md`
- `output/energy_policy_lockin_0901/02_high_priority_evidence_diagnosis.md`
- `output/energy_policy_lockin_0901/03_cox_boundary_sensitivity_audit.md`
- `output/energy_policy_lockin_0901/04_cox_main_update_plan.md`
- `output/energy_policy_lockin_0901/05_figure5_variable_choice_audit.md`
- `output/energy_policy_lockin_0901/HANDOFF_STATUS_20260907.md`
- `output/energy_policy_lockin_0901/NEXT_STEPS_FOR_NEW_REVIEWER_20260907.md`

### E.2 第三阶段 Cox sensitivity

**脚本**

- `code/sensitivity/cox_boundary_sensitivity_0907.py`

**结果目录**

- `result/tables/0907_cox_boundary_sensitivity/`
  - `boundary_event_audit.csv`
  - `cox_boundary_model_results.csv`
  - `cox_boundary_primary_comparison.csv`
  - `run_metadata.json`
- `result/figures/0907_cox_boundary_sensitivity/`
  - `cox_boundary_hr_comparison.png`
  - `cox_boundary_hr_comparison.pdf`

### E.3 第四阶段 Cox 新主图表

- `result/figures/0907_cox_boundary_main/`
  - `Figure_2_retirement_evidence_boundary_inclusive.png`
  - `Figure_2_retirement_evidence_boundary_inclusive.pdf`
- `result/tables/0907_cox_boundary_main/`
  - `Table_Cox_Main_Boundary_Inclusive.csv`
  - `Table_Cox_Main_Boundary_Inclusive_metadata.json`

### E.4 第五阶段 Figure 5 terminal candidate

- `result/figures/0907_figure5_terminal/`
  - `Figure_5_annual_composition_shares_terminal.png`
  - `Figure_5_annual_composition_shares_terminal.pdf`
- `result/tables/0907_figure5_terminal/`
  - `Figure_5_panel_a_terminal_audit.csv`
  - `Figure_5_panels_bc_audit.csv`
  - `Figure_5_terminal_metadata.json`

### E.5 第五阶段 Figure 5 consumption-relabel candidate

- `result/figures/0907_figure5_consumption_relabel/`
  - `Figure_5_annual_composition_shares_consumption_relabel.png`
  - `Figure_5_annual_composition_shares_consumption_relabel.pdf`
- `result/tables/0907_figure5_consumption_relabel/`
  - `Figure_5_panel_a_consumption_audit.csv`
  - `Figure_5_panels_bc_audit.csv`
  - `Figure_5_consumption_metadata.json`

## F. 绝对不要覆盖或直接修改的文件

除非用户明确宣布进入对应的正式修改阶段，不得覆盖或直接修改：

- `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`；
- `code/coal_retirement_survival_final_0820.py`；
- `code/plot_energy_policy_evidence_figures_0822.py`；
- `result/figures/energy_policy_lockin_0820/` 下的旧 Figure 1–5；
- `result/tables/0820_coal_retirement_survival_final/` 下的全部旧 Cox 结果；
- `data/gem_power_project_lifecycle/source/` 和其他原始 GEM 数据；
- `data/append_0518/`、`data/wind_*` 等 Wind 原始/准原始导出；
- `data/nea_renewable_monitoring/source_docs/`、`data/nea_power_reliability/source_pdfs/` 等 NEA 原始文档；
- `output/energy_policy_lockin_0820/` 下的历史稿件、BibTeX、投稿记录和 PDF/DOCX；
- 任何旧图、旧表、旧结果目录。

需要正式改稿时，应从最新 DOCX 新建有日期/版本号的副本，不覆盖 2026-09-01 基线稿。

## G. 当前仓库状态提醒

- 当前仓库位于 Windows 本地中文路径：`D:\大学\大三下\论文\投稿准备\jinmeng-transition`。执行命令时应使用 `-LiteralPath` 或完整引号，避免中文和空格路径解析错误。
- 当前 Python Launcher 可用，建议命令使用 `py -3 -X utf8`，而不是 WindowsApps 的 `python.exe` 别名。
- `lifelines 0.30.0` 已安装并可导入。
- `code/sensitivity/cox_boundary_sensitivity_0907.py` 明确导入并调用 `lifelines.CoxPHFitter`；被否决的自写 Cox partial likelihood/Efron/Hessian/sandwich estimator 没有生效。
- 项目仍缺统一 `requirements.txt`/lockfile、完整运行日志、Stata 外部包版本锁定、统一入口和最终 replication README/data dictionary。
- Wind 链依赖外部/专有数据访问；部分 NEA DOC/DOCX 解析脚本依赖 macOS `textutil`，在当前 Windows 环境不能原样重跑。
- 06 审计应优先区分“论文已使用但来源未写清”、“库内有来源元数据但 Methods 未引用”和“库内也无法确认”三种状态。

