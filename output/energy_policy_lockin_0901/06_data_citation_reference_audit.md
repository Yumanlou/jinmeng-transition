# Stage 06 data, citation, and reference audit

Audit date: 2026-09-08  
Runtime for Python checks: local conda environment `mcm` (`/Users/yumanlou/conda_env/MCM`, Python 3.13.11)  
Audit scope: read-only, except for creating this Markdown file. No DOCX, script, data, result, figure, or bibliography file was modified.

## A. Overall conclusion

The submission is not ready for manuscript revision until data provenance and policy-source documentation are tightened. The empirical evidence is mostly traceable to repository files, but several sources are proprietary, partial, late-starting, or only documented by variable names rather than by archived source records. The highest-risk issue is not the direction of the findings; it is whether a reviewer can verify where each variable and institutional claim came from without reconstructing the author's whole workstation.

The current worktree does not contain `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`. The handoff identifies that DOCX as the current audit object, but `output/energy_policy_lockin_0901/` currently contains only the Stage 01-05 audits, handoff files, and this file. Therefore, this Stage 06 audit uses `output/energy_policy_lockin_0820/manuscript.tex`, `output/energy_policy_lockin_0820/manuscript.docx`, the 0901 handoff summaries, and repository data/code as the auditable evidence base. Before formal revision, the missing 2026-09-01 DOCX must be restored or reintroduced into the repository/worktree.

The TeX/BibTeX inventory is now closed. Energy Policy `manuscript.tex` loads two BibTeX inputs: `../green_credit_transition_refs.bib` and `local_refs.bib`. The repository has three `.bib` files: `output/green_credit_transition_refs.bib`, `output/energy_policy_lockin_0820/local_refs.bib`, and `els-cas-templates/cas-refs.bib`. The Elsevier template bibliography is unrelated to the manuscript. `local_refs.bib` is not a complete bibliography; it is the Energy Policy increment, including GEM and added coal-power/transition literature. In the 0820 TeX, all 34 unique citation keys are present in the two loaded BibTeX files, and all 18 `local_refs.bib` entries are cited.

Two source-label corrections are mandatory. First, the Shanxi-Inner Mongolia policy-language result in the current manuscript should not be called a government-work-report result if it uses `data/policy_texts/` and `policy_eval_0518_full_chain.do`; that chain is provincial policy documents. The Li (2025) government-work-report corpus is a separate 31-province 2003-2023 corpus under `data/provincial_government_work_reports/`. Second, the GEM citation should distinguish Global Energy Monitor's official trackers from the Zenodo archive record `10.5281/zenodo.20843067`, which the repository metadata currently uses as an archived source record.

## B. Data-source gap list

The most serious gaps before submission are:

1. `Designed_for_Adjustment_2026-09-01.docx` is absent from the current worktree. This prevents direct re-extraction of the exact DOCX reference list, Methods, figure notes, table notes, declarations, and Data availability statement.
2. The base panel `data/final_data.1.3.4_did.csv` contains GDP, population, secondary-industry share, urbanization, environmental expenditure, and marketization variables, but the repository does not provide a visible unified source note or construction script for that base file. For those variables, the audit conclusion is: `无法从仓库确认`.
3. Wind-derived variables are documented at codebook level and often include Wind EDB codes, source names, units, and update dates, but underlying Wind access is proprietary and cannot be redistributed as an open replication source.
4. `data/wind_energy_transition_0718/README.md` records a `QUOTA_ERROR`; the partial Wind extraction is not a complete replacement for the existing yearbook/Wind variables.
5. Energy-balance `terminal` and `consumption` fields are distinct. Figure 5 should use the terminal/final-use candidate if the manuscript keeps final-use language.
6. Renewable consumption, grid utilization/curtailment, and coal-unit reliability begin late. They are constraint/context variables, not pre-policy moderators.
7. Primary policy documents are not archived in a repository `references/policy/` folder. The manuscript should not rely only on literature-map prose or unstable URLs for policy facts.
8. The current Data availability language promises documentation in replication materials, but a complete data dictionary, run-order file, dependency lock file, and non-redistributable data note are not yet present.

## C. Data provenance to add in Methods

### A-H source matrix

Columns: A = used in manuscript; B = current manuscript states source; C = repository raw/derived files; D = construction script; E = year coverage confirmed in repository; F = external/proprietary restriction; G = citation/data note needed; H = repository-confirmation status.

| Data item | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|
| GEM coal, wind, and solar trackers | Yes | Partly: GEM cited, but archive/source distinction blurred | `data/gem_power_project_lifecycle/source/GEM_GCPT_January_2026.xlsx`; `GEM_GWPT_February_2026.xlsx`; `GEM_GSPT_February_2026.xlsx`; `source_metadata.json` | `code/build_gem_power_project_lifecycle_0721.py` | province-year lifecycle 2000-2023; 2026 tracker snapshot | GEM terms/license; current snapshot, not historical vintages | Cite official GEM tracker releases; put Zenodo archive DOI/version in data availability or replication note | Confirmed in repository, with source-label correction needed |
| Coal unit start year, retired year, capacity, province, status | Yes | Partly | `data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv` | `code/build_gem_power_project_lifecycle_0721.py`; Cox scripts | Source snapshot has 6,520 China coal rows; active/historical rows 4,537; start-year nonmissing share 0.9586; retired-year nonmissing share 0.2638 | GEM tracker restrictions; missing dates/months | State annual-time convention and missing-start-year lower-bound caveat | Confirmed in repository |
| GEM coal additions, retirements, operating stock | Yes | Yes, but update Cox/Figure notes after Stage 03-04 | `gem_province_year_lifecycle_2000_2023.csv`; `gem_lifecycle_coverage.csv` | `build_gem_power_project_lifecycle_0721.py`; plotting scripts | 31 provinces x 2000-2023; Tibet absent in coal source and coded zero | GEM snapshot | Methods should say retrospective 2026 tracker reconstruction, not contemporaneous historical vintages | Confirmed in repository |
| GEM wind/solar additions and stocks | Yes | Yes | Same lifecycle panel and GEM source workbooks | `build_gem_power_project_lifecycle_0721.py` | 2000-2023; wind and solar active/historical source coverage differs by missing start years | GEM snapshot | Keep wind/solar stock language as capacity, not generation or displacement | Confirmed in repository |
| GEM project pipeline | Yes, as constraint/context | Partly | `data/gem_power_project_lifecycle/gem_province_current_pipeline_2026.csv`; `data/gem_project_pipeline_2026/gem_power_project_pipeline_province_2026.csv` | `build_gem_power_project_lifecycle_0721.py`; related pipeline scripts | 2026 current status snapshot, province-level | GEM snapshot | Describe as current pipeline, not historical project-flow series | Confirmed in repository |
| Provincial energy balances and five terminal-use fields | Yes | Partly | `data/append_0518/数据模板命名1.csv`; `data/append_0518/数据模板 5.csv`; `energy_balance_long.csv`; `energy_balance_panel.csv` | `code/build_energy_balance_panel.py` | terminal/energy-balance fields observed mainly 2000-2022 in merged panel; 686 nonmissing province-years for `energy5_int`, `coalterm_int`, `coalshare5` | Wind/yearbook exports; redistribution uncertain | Methods must define five-energy terminal basket as constructed and approximate, not total final energy or primary energy | Confirmed in repository, source provenance still needs cleaner citation |
| `energy5_int` | Yes | Partly | `data/final_data.1.3.4_did_full_0518.csv` and later merged panels | `build_energy_balance_panel.py`; alias in `build_append_0518_full_panel.py` | 686 nonmissing province-years, 2000-2022 | Wind/yearbook source | Define as five terminal fields converted to approximate 10k tce per GDP | Confirmed in repository |
| `coalterm_int` | Yes | Partly | Same as above | Same as above | 686 nonmissing province-years, 2000-2022 | Wind/yearbook source | Define as coal terminal-use approximate tce per GDP | Confirmed in repository |
| `coalshare5` | Yes | Partly | Same as above | Same as above | 686 nonmissing province-years, 2000-2022 | Wind/yearbook source | Define as coal terminal-use share of constructed five-energy terminal basket | Confirmed in repository |
| `coal_share_pctg` original statistical coal-consumption share | Yes, supporting | Weak | `data/final_data.1.3.4_did.csv` and merged panels | Base-panel construction not found | 744 nonmissing province-years, 2000-2023 | Source not documented in repository | Add original source and definition before submission | 无法从仓库确认 |
| Thermal installed capacity | Yes | Partly | `data/append_0518/数据模板命名.csv`; merged panels with `thermal_capacity_10k_kw` | `code/build_append_0518_full_panel.py` | 683 nonmissing province-years, 2000-2023 | Wind/yearbook exports | State source file and whether it is annual installed capacity stock | Confirmed in repository |
| Thermal generation | Yes | Partly | `data/append_0518/数据模板命名.csv`; merged panels with `thermal_generation_billion_kwh`; also NBS monthly alternative under `wind_energy_transition_0718` | `build_append_0518_full_panel.py`; `build_monthly_generation_stability_0718.py` for monthly alternative | annual: 743 nonmissing province-years, 2000-2023; monthly thermal coverage 2000-2023 | Wind/yearbook and Wind EDB | Do not mix annual yearbook/Wind series with NBS monthly YTD alternative without label | Confirmed in repository |
| Total capacity and total generation | Yes, as denominators | Partly | `data/append_0518/数据模板命名.csv`; merged panels | `build_append_0518_full_panel.py` | 2000-2023, with specific missingness by variable | Wind/yearbook | Define shares as thermal/total annual provincial sums | Confirmed in repository |
| GDP | Yes, control and denominator | No sufficient source note | `data/final_data.1.3.4_did.csv` | Base-panel construction not found | 744 nonmissing province-years, 2000-2023 | Unknown | Add original source, unit, deflator/current-price status, and any transformations | 无法从仓库确认 |
| Population | Yes, control | No sufficient source note | `data/final_data.1.3.4_did.csv` | Base-panel construction not found | 744 nonmissing province-years, 2000-2023 | Unknown | Add source and unit | 无法从仓库确认 |
| Secondary-industry share | Yes, control | No sufficient source note | `sec_val`, `sec_pctg` in `final_data.1.3.4_did.csv` | Base-panel construction not found | 744 nonmissing province-years, 2000-2023 | Unknown | Add source and construction formula | 无法从仓库确认 |
| Urbanization | Yes, control | No sufficient source note | `urban_population`, `urbanization_rate` in base panel | Base-panel construction not found | 589 nonmissing province-years, 2005-2023 | Unknown | Add source, population definition, and missing-coverage note | 无法从仓库确认 |
| Environmental expenditure | Yes, control | No sufficient source note | `env_expenditure`, `env_exp_share` in base panel | Base-panel construction not found | 527 nonmissing province-years, 2007-2023 | Unknown | Add fiscal item source and share denominator | 无法从仓库确认 |
| Marketization index | Yes, control | No sufficient source note | `market_index` and subindexes in base panel | Base-panel construction not found | 744 nonmissing province-years, 2000-2023 | Likely licensed/proprietary, but repository does not confirm | Add exact source edition, citation, access restriction, and interpolation if any | 无法从仓库确认 |
| Mining employment | Yes, resource dependence | Partly | `data/wind_resource_dependency/wind_resource_dependency_*`; merged codebook | `code/fetch_wind_resource_dependency.py`; `merge_resource_dependency_panel.py` | 650 observations, 31 provinces, 2003-2023 | Wind EDB; provincial statistical bureaus | Cite Wind/provincial-statistical-bureau source and define denominator | Confirmed in repository |
| Coal-mining assets | Yes, resource dependence | Partly | Same Wind resource-dependency files | Same scripts | 465 observations, 26 provinces, 2000-2023; constructed share 433 observations, 25 provinces, 2005-2023 | Wind EDB; provincial statistical bureaus | Note incomplete province coverage | Confirmed in repository |
| Resource-tax revenue | Yes, resource dependence | Partly | Same Wind resource-dependency files | Same scripts | 705 observations, 31 provinces, 2000-2023 | Wind EDB; provincial statistical bureaus | Define public-budget denominator for share | Confirmed in repository |
| Raw-coal output | Yes, extension | Partly | `data/wind_resource_dependency/`; `data/wind_raw_coal_output/`; merged panel fields | `fetch_wind_resource_dependency.py`; `build_resource_dependence_v2_0716.py` | Wind resource coverage shows 110 observations, 6 provinces, 2000-2023; final merged panel has 545 nonmissing observations after additional merge | Wind EDB; source-quality flags | Explain partial direct Wind coverage and added raw-coal source-quality flags before using | Partly confirmed; source chain needs a clearer note |
| Renewable consumption | Yes, constraint/Figure 3 | Partly | `data/nea_renewable_consumption/source_docs/`; `nea_renewable_consumption_province_2015_2023.csv`; coverage CSV | `code/build_nea_renewable_consumption_panel_0718.py` | 31 provinces, 2015-2023; 2023 amount fields missing while share fields exist | NEA public reports, parsed from DOC/DOCX | Cite NEA monitoring reports and note late start | Confirmed in repository |
| Renewable utilization/curtailment | Yes, constraint | Partly | `data/wind_grid_absorption/`; NEA utilization fields in merged panel | `merge_resource_dependency_panel.py`; Wind grid scripts | Wind/solar utilization hours 2018-2023; NEA utilization/curtailment rates 2020-2023 | Wind EDB and NEA reports | Do not use as pre-policy moderator; label coverage | Confirmed in repository |
| Coal-unit reliability/standby | Yes, constraint | Partly | `data/nea_power_reliability/source_pdfs/`; `nea_coal_unit_reliability_province_2018_2023.csv`; coverage CSV | `code/build_nea_coal_reliability_panel_0718.py` | 30 reported provinces, 2018-2023; utilization hours missing for 2021-2023 but operating/standby hours present | NEA public PDFs; parsed values | Cite annual reliability reports; explain 30-province coal-unit coverage | Confirmed in repository |
| Monthly generation | Yes, as stability/grid context | Partly | `data/monthly_generation_stability/`; raw `data/wind_energy_transition_0718/wind_energy_transition_raw_long.csv` | `code/build_monthly_generation_stability_0718.py` | thermal 2000-2023, wind 2013-2023, solar 2016-2023; coverage differs by technology | Wind EDB/NBS monthly YTD; quota issue in broader extraction | Label as monthly YTD-derived increments, with negative-increment flags | Confirmed in repository |
| Provincial government work reports | Yes only if using Li corpus; current Jin-Meng sentence likely mislabeled | Partly | `data/provincial_government_work_reports/source/pone.0324713.s001.zip`; extracted files; `provincial_policy_attention_panel_2003_2023.csv` | `code/build_national_provincial_policy_attention_0721.py` | 31 provinces, one report per province-year, 2003-2023 | Li (2025) PLOS ONE supplement, CC BY 4.0 | Cite Li (2025), DOI `10.1371/journal.pone.0324713`, and say dictionary frequency is attention, not support | Confirmed in repository |
| Jin-Meng provincial policy documents | Yes for existing Shanxi/Inner Mongolia policy-language result | Weak in manuscript label | `data/policy_texts/shanxi_policy_documents_2000_2023.csv`; `nmg_policy_documents_2000_2023.csv`; indices and combined panel | `code/build_policy_text_indices.py`; `code/policy_eval_0518_full_chain.do` | 2000-2023 for Shanxi and Inner Mongolia policy-document panel | Local collected policy texts; source URLs/official archive not fully documented in a citation-ready form | Call this provincial policy-document text, not government work reports; add source collection note | Confirmed as repository chain; source provenance still incomplete |
| Wind-derived variables, all groups | Yes, many controls/outcomes/context fields | Partly | `data/append_0518/`; `data/wind_*`; codebooks and metadata | Multiple `fetch_*`, `build_*`, and merge scripts | Varies by variable; coverage files exist for many modules | Wind proprietary access and quota limits | Data availability must separate redistributable derived values from non-redistributable Wind raw/source files | Confirmed at codebook level; external access remains a replication restriction |

### Methods text that should be added or tightened

The Methods section should add a compact data paragraph with three layers.

First, the GEM asset layer should state that coal, wind, and solar project histories are reconstructed from the January-February 2026 Global Energy Monitor tracker snapshots; that coal units are at least 30 MW; that annual stocks, additions, and retirements are retrospective reconstructions from reported start and retirement years; and that missing early start years make early stocks lower bounds.

Second, the provincial operating layer should state that `energy5_int`, `coalterm_int`, and `coalshare5` use five terminal-consumption fields: coal, oil products, LPG, natural gas, and electricity. They are converted into approximate standard-coal equivalents for a constructed five-energy terminal/final-use basket. This is not total primary energy and not complete total final energy.

Third, the constraint layer should state that resource-dependence fields come from Wind EDB/provincial statistical sources; renewable-consumption fields come from NEA annual monitoring reports from 2015; coal-unit reliability fields come from NEA reliability reports from 2018; monthly generation stability fields are derived from Wind/NBS monthly YTD series; and later-starting fields are descriptive constraints, not pre-policy treatment moderators.

## D. In-text citation and reference-list check

The TeX citation check found 34 unique citation keys in `output/energy_policy_lockin_0820/manuscript.tex`. All are present in the union of `output/green_credit_transition_refs.bib` and `output/energy_policy_lockin_0820/local_refs.bib`. No cited key is missing from the loaded BibTeX sources. All 18 entries in `local_refs.bib` are cited by the TeX manuscript.

The loaded bibliography structure is:

| File | Role | Entries | Submission relevance |
|---|---|---:|---|
| `output/green_credit_transition_refs.bib` | Main inherited bibliography | 48 | Loaded by manuscript |
| `output/energy_policy_lockin_0820/local_refs.bib` | Energy Policy increment | 18 | Loaded by manuscript |
| `els-cas-templates/cas-refs.bib` | Elsevier template/sample bibliography | not part of manuscript | Ignore for submission |

`local_refs.bib` should not be treated as complete. It is an increment layered on top of `green_credit_transition_refs.bib`. This matters because changing or exporting only `local_refs.bib` would silently drop the older green-credit, lock-in, transition, and regional-development references.

The current 0820 TeX does not cite the policy documents listed in `literature_map_50.md` except `cbrc2012`. If the revised manuscript keeps the institutional timeline for the 2012-2023 policy mix, it needs explicit primary-policy references, not only academic citations or a prose statement.

The GEM reference needs correction. Current `gem2026` uses `author = {{Global Energy Monitor}}` and `url = {https://zenodo.org/records/20843067}`. Repository metadata says the source record is Zenodo DOI `10.5281/zenodo.20843067`, original source is "Global Energy Monitor power trackers", and license is CC BY 4.0. Global Energy Monitor's official tracker pages are the proper source for tracker identity and recommended tracker citation; the Zenodo DOI should be treated as an archive/version record unless its landing page is verified to have Global Energy Monitor as creator and the exact tracker title/release. Do not collapse these into a single unqualified "Global Energy Monitor, Zenodo" reference.

Recommended split:

| Item | Where it belongs | Suggested handling |
|---|---|---|
| GEM official tracker release | Reference list or data citation | Cite Global Energy Monitor, `Global Coal Plant Tracker`, January 2026 release; `Global Wind Power Tracker`, February 2026 release; `Global Solar Power Tracker`, February 2026 release, with official tracker URLs and access date |
| Zenodo/Modelblocks archive DOI `10.5281/zenodo.20843067` | Data availability / replication note, or separate archived-data reference if verified | State that the working files were obtained/archived from Zenodo record `10.5281/zenodo.20843067`; verify creator/title/version before using it as the sole data citation |

## E. Required primary policy files

The manuscript should not use academic literature as a substitute for policy facts. Each institutional claim should map to an issuing body, title, date, and official page/PDF archived in the replication folder. The repository currently does not contain a citation-ready `references/policy/` archive, so each row below is required before submission.

| Policy fact or manuscript use | Required primary file | Current repository status | Needed action |
|---|---|---|---|
| 2012 green-credit institutional window and bank environmental/social-risk requirements | China Banking Regulatory Commission, 2012, `Green Credit Guidelines` / `绿色信贷指引`, CBRC Notice No. 4 | Cited as `cbrc2012` with gov.cn URL in `green_credit_transition_refs.bib`; no archived PDF/source folder found | Keep citation, archive official Chinese text/PDF, and cite only what the text states |
| Major concurrent air-pollution policy affecting coal-intensive regions | State Council, 2013, `Air Pollution Prevention and Control Action Plan` / `大气污染防治行动计划` | Listed in `literature_map_50.md`; not in loaded BibTeX; no archive found | Add primary citation after author approval and use to limit causal attribution |
| Power-market reform, dispatch/pricing/trading context | CPC Central Committee and State Council, 2015, Document No. 9 / `关于进一步深化电力体制改革的若干意见` | Listed in literature map only | Add official source and do not treat as uniform province-level treatment |
| Planning-era coexistence of capacity control, cleaner coal, renewable build-out, and reliability | NDRC and NEA, 2016, `Electric Power Development Thirteenth Five-Year Plan (2016-2020)` | Listed in literature map only | Archive official PDF/text and quote exact targets/clauses |
| Renewable electricity consumption responsibility/absorption mechanism | NDRC and NEA, 2019, renewable electricity consumption guarantee mechanism notice | Listed in literature map only | Add primary citation; connect to consumption/absorption, not direct coal retirement |
| Dual-carbon high-level framework | CPC Central Committee and State Council, 2021, dual-carbon opinions | Listed in literature map only | Add primary citation as goal/principle framework, not plant retirement schedule |
| Carbon Peaking Action Plan by 2030 | State Council, 2021, `2030年前碳达峰行动方案` | Listed in literature map only | Add official source and quote coal-power provisions exactly |
| Coal-unit upgrading and "three reforms" | NDRC and NEA, 2021, national coal-fired power unit upgrading/retrofit implementation plan | Listed in literature map only | Add official source; this is strong evidence for operation/flexibility/heating transformation, not fleet-wide exit |
| Modern energy-system planning, security, grid, storage, renewable development | NDRC and NEA, 2022, `Fourteenth Five-Year Plan for a Modern Energy System` | Listed in literature map only | Add official source and connect to system/replacement context |
| Coal-fired power capacity-pricing mechanism | NDRC, 2023, coal-fired power capacity-pricing mechanism notice | Listed in literature map only | Add official source; use as capacity/adequacy context, not an identified cause of historical retirement |

The Jin-Meng policy-document chain and Li (2025) work-report chain must remain separate:

| Chain | Repository source | Script | Output/use | Correct label |
|---|---|---|---|---|
| Shanxi/Inner Mongolia provincial policy documents | `data/policy_texts/*_policy_documents_2000_2023.csv` | `code/build_policy_text_indices.py`; `code/policy_eval_0518_full_chain.do` | `jinmeng_policy_text_year_panel_2000_2023.csv`; Jin-Meng path regressions | Provincial policy documents |
| Li (2025) government work reports | `data/provincial_government_work_reports/source/pone.0324713.s001.zip` and extracted files | `code/build_national_provincial_policy_attention_0721.py` | 31-province 2003-2023 dictionary-frequency panel | Provincial government work reports, Li (2025) corpus |

If the manuscript sentence says "Government-work-report text supports only a narrow contrast" while relying on `Table_0518_7_JinMeng_Policy_Text_Path`, the label is wrong. The sentence should instead say "provincial policy-document text" unless the Li (2025) chain is separately audited and its results are actually used.

## F. Recommended supplemental literature

Only 3-5 additions should be considered, and only from `output/energy_policy_lockin_0820/literature_map_50.md`. The goal is to close argument gaps, not decorate the reference list.

Recommended shortlist:

| Source | Why it is worth adding | Where to use | Boundary |
|---|---|---|---|
| Heerma van Voss et al. (2022), `Sensitive intervention points in China's coal phaseout`, Energy Policy, DOI `10.1016/j.enpol.2022.112797` | Direct Energy Policy comparator on Chinese coal-phaseout leverage points | Discussion / policy architecture | Scenario/political-economy source, not evidence for this paper's historical estimates |
| Yan et al. (2024), `Cost-effectiveness uncertainty may bias the decision of coal power transitions in China`, Nature Communications, DOI `10.1038/s41467-024-46549-5` | Gives micro-foundation for why plant/owner decisions may not exit even when aggregate indicators improve | Discussion / limitations | Do not claim the paper observes owner cost expectations |
| Yu et al. (2023), `Combining mandatory coal power phaseout and emissions trading in China's power sector`, Energy Economics, DOI `10.1016/j.eneco.2023.106694` | Supports the distinction between price/finance signals and mandatory retirement instruments | Discussion | Modelled comparison, not observed policy evaluation |
| Chen et al. (2022), `Winding down the wind power curtailment in China`, Renewable & Sustainable Energy Reviews, DOI `10.1016/j.rser.2022.112725` | Balances the constraint story by showing absorption improvement is real policy/system progress | Constraint interpretation / Figure 3 | Better absorption does not equal observed coal-unit retirement |
| Wang et al. (2023), `Accelerating the energy transition towards photovoltaic and wind in China`, Nature, DOI `10.1038/s41586-023-06180-8` | Prevents the argument from reading as "renewables cannot work"; useful positive counterweight | Introduction / Discussion | Potential and acceleration are not direct evidence of asset exit |

If space is tight, use three: Heerma van Voss et al. (2022), Yu et al. (2023), and Chen et al. (2022). That combination covers coal-phaseout intervention design, instrument-margin distinction, and renewable absorption without expanding into a generic literature review.

## G. Data availability / replication package risks

The current Data availability statement is too broad for the actual repository state. It says the provincial panel, processing scripts, outputs, and derived project-lifecycle measures are available upon reasonable request subject to Wind and GEM terms. That is directionally acceptable, but it needs a sharper replication note.

Required additions:

1. A data dictionary listing each manuscript variable, source file, construction script, unit, coverage, and redistribution status.
2. A run-order file separating reproducible local steps from Wind/API/manual-source steps.
3. A Python environment file for the conda `mcm` environment or a minimal reproducible requirements file.
4. A Stata version and package list for `reghdfe`, `estout/outreg2`, and any other external packages used by the `.do` files.
5. A policy-source archive folder containing the exact official Chinese policy pages/PDFs cited.
6. A clear statement that Wind raw exports and Wind EDB-derived source files may be proprietary and may need to be replaced by access instructions rather than redistribution.
7. A separate GEM note distinguishing official tracker releases from the Zenodo archive record used in this repository.

Residual risks:

| Risk | Severity | Why it matters |
|---|---|---|
| Missing 2026-09-01 DOCX in current worktree | High | Direct DOCX reference-list and declarations cannot be rechecked here |
| Base-panel source provenance unknown | High | Controls and several legacy outcomes cannot be defended from repository evidence alone |
| Policy facts not backed by archived primary texts | High | A reviewer can challenge institutional claims even if academic citations are correct |
| GEM citation conflates tracker and archive | Medium-high | Data citation may be formally wrong or at least ambiguous |
| Wind proprietary and quota-limited data | Medium-high | Replication cannot be fully open without access instructions |
| Late-starting constraint variables | Medium | Interpretation risk if presented as causal moderators |
| TeX bibliography split across two files | Medium | Manageable, but dangerous if exporting only `local_refs.bib` |

## H. Pre-submission priority ranking

1. Restore or locate `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx` in this worktree, then re-run the DOCX extraction against the actual current manuscript.
2. Create the missing source-provenance note for `data/final_data.1.3.4_did.csv`, especially GDP, population, secondary-industry share, urbanization, environmental expenditure, marketization index, `coal_share_pctg`, emissions, and CO2 fields.
3. Archive and cite the ten required primary policy files before revising institutional/policy paragraphs.
4. Correct the Jin-Meng text label: provincial policy documents are not Li (2025) government work reports.
5. Correct the GEM data citation by separating official tracker release citation from Zenodo archive/version citation.
6. Use the locked Stage 03-05 empirical decisions in the formal DOCX revision: boundary-inclusive Cox main numbers and terminal/final-use Figure 5.
7. Add a concise replication README, data dictionary, and environment/dependency note before submission.
8. Add no more than 3-5 supplemental references from `literature_map_50.md`, prioritizing argument gaps over reference-list size.

