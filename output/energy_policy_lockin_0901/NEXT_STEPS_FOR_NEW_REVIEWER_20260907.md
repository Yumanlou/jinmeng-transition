# Energy Policy 新审阅者后续步骤

更新日期：2026-09-07

## A. 接手后的必读顺序

请按以下顺序阅读，不要先改论文：

1. `output/energy_policy_lockin_0901/HANDOFF_STATUS_20260907.md`  
   用途：掌握已锁定决策、新资产、禁止覆盖的文件和第六阶段中途进度。
2. `output/energy_policy_lockin_0901/03_cox_boundary_sensitivity_audit.md`  
   用途：理解 Cox annual-time 问题、新主规格和 legacy 规格的边界。
3. `output/energy_policy_lockin_0901/04_cox_main_update_plan.md`  
   用途：掌握新 Figure 2、Cox 主表和论文数字替换要求。
4. `output/energy_policy_lockin_0901/05_figure5_variable_choice_audit.md`  
   用途：掌握 Figure 5 terminal 选择、新数字和必须删除的旧标签。
5. `output/energy_policy_lockin_0901/02_high_priority_evidence_diagnosis.md`  
   用途：查看 Cox 旧数字如何产生、Figure 5 字段冲突和 DOCX 缺失的两张表。
6. `output/energy_policy_lockin_0901/01_evidence_chain_audit.md`  
   用途：查看整体证据链、结果文件和复现限制。注意：其 Cox 样本冲突初判已由 02 更正。
7. `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`  
   用途：定位当前待改的 Abstract、Methods、Results、notes、tables、Data availability 和 declarations。只读，直到用户明确进入正式改稿阶段。
8. `output/energy_policy_lockin_0820/literature_map_50.md`  
   用途：只从已筛选的 50 条中选择真正必要的补充文献和一手政策文件。
9. `output/energy_policy_lockin_0820/local_refs.bib` 和 `output/energy_policy_lockin_0820/submission_notes.md`  
   用途：核对已有 BibTeX 增量条目、GEM 数据引用和投稿包的人工确认项。

## B. 如何继续第六阶段

第六阶段最终只应生成：

`output/energy_policy_lockin_0901/06_data_citation_reference_audit.md`

建议按以下步骤继续。

### B.1 先重建论文引用和 bibliography 底表

1. 从 DOCX `word/document.xml` 提取全部正文 author-year citations 和 reference-list 条目。
2. 重新执行上一轮被中断的 TeX/BibTeX 检查：查找 `manuscript.tex` 的 `addbibresource`/参考文献输入和仓库全部 `.bib`。
3. 区分“DOCX 参考文献列表完整”和“复现包的 BibTeX 源完整”；`local_refs.bib` 可能只是增量文库，不得默认其为全部条目。
4. 对 DOI、年份、题名、期刊、页码/文章号做系统对照；优先使用 Crossref/期刊官方页，不要用二手文献表替代主记录。
5. 单独审查 GEM 条目：当前 Zenodo DOI 指向收录 GEM releases 的 Modelblocks archive，不是以 Global Energy Monitor 为创建者的同名单一数据集。建议将 GEM 官方 tracker release citation 与 archive DOI/版本记录分开处理。

### B.2 完成用户要求的逐变量 A–H 矩阵

对下列每一项都列出：A 论文是否使用；B 当前是否说明来源；C 库内原始/派生文件；D 构造脚本；E 年份覆盖；F 外部/专有限制；G 投稿前需补的 citation/data note；H 库内不能确认时明确写“无法从仓库确认”。

- GEM coal/wind/solar trackers 及 coal unit start year, retired year, capacity, province, status；
- provincial energy balances 及五个 terminal-use 字段；
- `energy5_int`、`coalterm_int`、`coalshare5`；
- thermal installed capacity 和 thermal generation；
- GDP、population、secondary-industry share、urbanization、environmental expenditure、marketization index；
- mining employment、coal-mining assets、resource-tax revenue、raw-coal output；
- renewable consumption、utilization/curtailment、coal-unit reliability/standby；
- monthly generation、provincial government work reports、project pipeline；
- 所有 Wind-derived variables。

已知的关键入口包括：

- 能源平衡：`data/append_0518/数据模板命名1.csv`、`data/append_0518/数据模板 5.csv`→`code/build_energy_balance_panel.py`。
- 电力装机/发电：`data/append_0518/` 下 Wind 导出和整理表→`code/build_append_0518_full_panel.py`。
- 资源依赖：`data/wind_resource_dependency/`→`fetch_wind_resource_dependency.py`、`build_resource_dependence_v2_0716.py`、`merge_resource_dependency_panel.py`。
- NEA renewable consumption：`data/nea_renewable_monitoring/source_docs/`→`build_nea_renewable_consumption_panel_0718.py`。
- NEA coal reliability：`data/nea_power_reliability/source_pdfs/`→`build_nea_coal_reliability_panel_0718.py`。
- Monthly generation：`data/wind_energy_transition_0718/wind_energy_transition_raw_long.csv`→`build_monthly_generation_stability_0718.py`。
- GEM lifecycle/pipeline：`data/gem_power_project_lifecycle/source/`→`build_gem_power_project_lifecycle_0721.py`。
- Government work reports：`data/provincial_government_work_reports/source/`→`build_national_provincial_policy_attention_0721.py`，语料来自 Li (2025), PLOS ONE, DOI `10.1371/journal.pone.0324713`。
- 晋蒙旧 policy-language 结果：`data/policy_texts/`→`build_policy_text_indices.py`→`policy_eval_0518_full_chain.do`。这不等于 government-work-report corpus。

### B.3 先解决两个高优先级来源错位

1. **Government-work-report 标签错位**：查明正文晋蒙句子应对应哪一条结果链。如对应 `Table_0518_7_JinMeng_Policy_Text_Path`，应称 provincial policy documents，不应称 government work reports；如要使用后者，需另行审核其结果，不得直接以名称替换。
2. **基础面板来源缺失**：`final_data.1.3.4_did.csv` 对 GDP、population、secondary share、urbanization、environmental expenditure 和 marketization index 没有可见的统一来源文档。应先查仓库；找不到就在 06 中写“无法从仓库确认”，并列为必须由作者补充的一手 provenance。

### B.4 完成政策一手文件矩阵

对正文每一处 2012 Green Credit Guidelines、post-2012 policy mix、clean utilization、renewable deployment/consumption、reliability、capacity/flexibility role 和 coal-power transition policy 句子，列出能直接支撑的一手政策文件。

优先核对 `literature_map_50.md` 中的：

- China Banking Regulatory Commission (2012), Green Credit Guidelines；
- State Council (2013), Air Pollution Prevention and Control Action Plan；
- CPC Central Committee and State Council (2015), power-sector reform Document No. 9；
- NDRC and NEA (2016), Electric Power Development Thirteenth Five-Year Plan；
- NDRC and NEA (2019), renewable electricity consumption guarantee mechanism；
- CPC Central Committee and State Council (2021), dual-carbon opinions；
- State Council (2021), Carbon Peaking Action Plan by 2030；
- NDRC and NEA (2021), National Coal-Fired Power Unit Upgrading Plan；
- NDRC and NEA (2022), Fourteenth Five-Year Plan for a Modern Energy System；
- NDRC (2023), coal-fired power capacity-pricing mechanism。

引用应指向发文机关/政府官方页或官方 PDF，不用学术二手文献替代一手政策依据。不要用 2024 年文件解释 2012–2023 的估计结果。

### B.5 精简补充文献

不要重新搜索大型文献库。优先从 `literature_map_50.md` 中选择 3–5 篇真正填补论证缺口的文献。当前值得优先复核的是：

- Heerma van Voss and Rafaty (2022), *Energy Policy*：China coal-phaseout intervention points；
- Yan et al. (2024), *Nature Communications*：coal-power transition cost-effectiveness uncertainty；
- Yu et al. (2023), *Energy Economics*：mandatory phaseout versus emissions trading；
- Chen et al. (2022), *Renewable and Sustainable Energy Reviews*：China wind curtailment/absorption；
- Wang et al. (2023), *Nature*：China wind/PV transition potential，用作对“过度悲观”解读的平衡。

是否引用应由其能否支撑一个现有缺口决定，而不是为了增加文献数量。

### B.6 按用户指定结构写 06

`06_data_citation_reference_audit.md` 必须使用：

A. 总体结论  
B. 数据来源缺口清单  
C. Methods 中应补充的 data provenance  
D. 文内引用—参考文献对应检查  
E. 必补政策文件  
F. 建议补充文献  
G. Data availability / replication package 风险  
H. 投稿前优先级排序

该阶段仍不修改 DOCX、代码、数据、图表或 bibliography。

## C. 继续第六阶段的推荐 Codex 指令

可将以下指令原样交给 Codex：

```text
继续 Energy Policy 投稿终审第六阶段。

先读取：
output/energy_policy_lockin_0901/HANDOFF_STATUS_20260907.md
output/energy_policy_lockin_0901/NEXT_STEPS_FOR_NEW_REVIEWER_20260907.md
output/energy_policy_lockin_0901/01_evidence_chain_audit.md
output/energy_policy_lockin_0901/02_high_priority_evidence_diagnosis.md
output/energy_policy_lockin_0901/03_cox_boundary_sensitivity_audit.md
output/energy_policy_lockin_0901/04_cox_main_update_plan.md
output/energy_policy_lockin_0901/05_figure5_variable_choice_audit.md
output/energy_policy_lockin_0820/literature_map_50.md
output/energy_policy_lockin_0820/local_refs.bib
output/energy_policy_lockin_0820/submission_notes.md

只读完成 data/citation/reference audit，并仅生成：
output/energy_policy_lockin_0901/06_data_citation_reference_audit.md

重点：
1. 对用户指定的每一个数据项建立 A–H 来源矩阵；库内不能确认时必须明写“无法从仓库确认”。
2. 重新检查 TeX 加载的完整 bibliography，因上一条 addbibresource/.bib 命令已中断。
3. 区分晋蒙 provincial policy-document 链与 Li (2025) government-work-report 链，不要把两者合并。
4. 复核 GEM 官方 tracker citation 与 Zenodo Modelblocks archive DOI 的作者/标题对应。
5. 政策事实必须用一手政策文件；学术文献不得替代一手文件。
6. 补充文献仅从 literature_map_50.md 中筛选必要/高价值条目，不大规模扩张。

不修改论文 DOCX、代码、原始数据、图表、旧结果或参考文献文件。
```

## D. 完成第六阶段后的后续顺序

1. **可复现性修复**  
   建立 requirements/lockfile、运行日志、统一入口、数据字典、source metadata 和 replication README；先解决不改变估计结果的基础设施问题。
2. **正式修改论文 DOCX**  
   必须由用户明确授权；从 2026-09-01 基线 DOCX 新建版本，不覆盖旧稿。
3. **插入新 Figure 2、Figure 5 和两张缺失表**  
   Figure 2 使用 `0907_cox_boundary_main`；Figure 5 使用 `0907_figure5_terminal`；插入 boundary-inclusive Cox 主表和 provincial FE/supporting-results table。
4. **更新核心段落和声明**  
   依次更新 Abstract、Methods、Results、Figure notes、table notes、Data availability 和 AI declaration；同时完成政策/数据来源引用。
5. **语言与 AI 痕迹终修**  
   在数字、变量名称、引用和图表锁定后再做，避免润色覆盖方法限定。
6. **Energy Policy 格式终检**  
   核对字数、abstract、keywords、highlights、figure/table placement、references、data statement、funding、competing interests、AI declaration、title page 和投稿系统当时要求。

## E. 权限规则

- 只读命令可以执行，包括检索、读取、计数、哈希、文本提取和环境检查。
- 用户指定的新审计文件、新图表目录和新结果目录可以在其明确阶段范围内新建。
- 修改原始数据、原始/旧脚本、旧结果、旧图表、参考文献文件或主论文 DOCX 前，必须获得用户针对该阶段的明确确认。
- 不得改写 Cox 估计器，不得手写 partial likelihood、ties、gradient、Hessian、sandwich variance 或任何替代 Cox 模型。
- Cox 相关重跑必须继续使用与 0820 一致的 `lifelines.CoxPHFitter`；除非用户明确改变研究设计，只能修改已授权的时间/事件编码。
- 不得为了“结果更好看”选择模型、变量或文献。

## F. 已锁定问题的处理原则

以下问题不要重新讨论，除非发现可验证的新证据：

- Cox 主规格是 boundary-inclusive end-of-reported-year；
- Cox 新口径是 4,326 / 1,078 / 12,470；
- 旧 4,323 / 952 / 12,344 是 legacy/robustness；
- 新 Figure 2 已生成且应用于新主稿；
- Figure 5 推荐 terminal/final-use candidate；
- 68.2%→58.8% 属于 consumption basket，不是 final use；
- terminal 煤炭份额是 44.8436%→21.1224%；
- post-2012 Cox 各期不显著不是正式 post-versus-pre equality test；
- Figure 3 只是三维描述，不显示全部 constraints。

如出现新证据，必须记录其文件路径、变量/代码位置、与已有证据的冲突方式，再请用户决定是否重开已锁定问题。

