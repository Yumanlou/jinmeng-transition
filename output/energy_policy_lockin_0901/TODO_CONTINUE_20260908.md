# Energy Policy continuation todo

Created: 2026-09-08  
Working branch: `codex/pr-1-handoff-energy-policy-20260907`  
Current status: PR handoff package has stages 01-05 complete. Stage 06 is not yet written. The 2026-09-01 DOCX has not been revised.

## 0. Branch and remote setup

- [x] Fetch PR #1 into a local branch.
- [x] Switch working tree to `codex/pr-1-handoff-energy-policy-20260907`.
- [ ] After the new remote repository is created, add it as a separate remote. Do not replace `origin` unless that is intentional.
- [ ] Push this branch to the new remote.
- [ ] Confirm the new remote contains the 7 handoff Markdown files, new Cox/Figure 5 assets, and this todo file.

Suggested commands after the new repo exists:

```bash
git remote add newrepo <NEW_REMOTE_URL>
git push -u newrepo codex/pr-1-handoff-energy-policy-20260907
```

If the new repo should become the main remote later, decide that explicitly after confirming the push.

## 1. Immediate task: finish Stage 06

Target output:

- [ ] `output/energy_policy_lockin_0901/06_data_citation_reference_audit.md`

Do this as a read-only audit except for creating the Stage 06 Markdown file.

- [ ] Read the handoff files in this order:
  - `output/energy_policy_lockin_0901/HANDOFF_STATUS_20260907.md`
  - `output/energy_policy_lockin_0901/NEXT_STEPS_FOR_NEW_REVIEWER_20260907.md`
  - `output/energy_policy_lockin_0901/03_cox_boundary_sensitivity_audit.md`
  - `output/energy_policy_lockin_0901/04_cox_main_update_plan.md`
  - `output/energy_policy_lockin_0901/05_figure5_variable_choice_audit.md`
  - `output/energy_policy_lockin_0901/02_high_priority_evidence_diagnosis.md`
  - `output/energy_policy_lockin_0901/01_evidence_chain_audit.md`
- [ ] Extract the current DOCX text, reference list, Methods, Results, Data availability, declarations, figure notes, and table notes from `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`.
- [ ] Rebuild a citation/reference check table from the DOCX author-year citations and reference list.
- [ ] Re-run the interrupted TeX/BibTeX inventory:
  - find every `.bib` file in the repository;
  - inspect `manuscript.tex` and any included TeX files for bibliography inputs;
  - decide whether `local_refs.bib` is a complete bibliography or only an increment.
- [ ] Audit DOI, title, journal, year, page/article number, and author spelling for all references that matter for the submission.
- [ ] Write a variable-level A-H source matrix:
  - A: whether the manuscript uses the item;
  - B: whether the manuscript currently states the source;
  - C: raw/derived files in the repository;
  - D: construction script;
  - E: year coverage;
  - F: external/proprietary restriction;
  - G: citation/data note needed before submission;
  - H: if not confirmable from the repository, state `无法从仓库确认`.
- [ ] Cover at least these data groups in the A-H matrix:
  - GEM coal, wind, and solar trackers;
  - coal unit start year, retired year, capacity, province, and status;
  - provincial energy balances and five terminal-use fields;
  - `energy5_int`, `coalterm_int`, and `coalshare5`;
  - thermal installed capacity and thermal generation;
  - GDP, population, secondary-industry share, urbanization, environmental expenditure, and marketization index;
  - mining employment, coal-mining assets, resource-tax revenue, and raw-coal output;
  - renewable consumption, utilization/curtailment, coal-unit reliability/standby;
  - monthly generation, provincial government work reports, project pipeline;
  - all Wind-derived variables.
- [ ] Separate the two policy-text chains:
  - Jinmeng provincial policy-document chain: `data/policy_texts/` -> `build_policy_text_indices.py` -> `policy_eval_0518_full_chain.do`;
  - Li (2025) provincial government-work-report corpus chain: `data/provincial_government_work_reports/source/` -> `build_national_provincial_policy_attention_0721.py`.
- [ ] Fix the source-label diagnosis in the audit: do not let "government work reports" stand in for Jinmeng provincial policy documents unless the evidence chain actually supports that.
- [ ] Build a primary-policy-file matrix for every manuscript sentence relying on:
  - 2012 Green Credit Guidelines;
  - 2013 Air Pollution Prevention and Control Action Plan;
  - 2015 power-sector reform Document No. 9;
  - 2016 Thirteenth Five-Year power plan;
  - 2019 renewable electricity consumption guarantee mechanism;
  - 2021 dual-carbon opinions;
  - 2021 Carbon Peaking Action Plan;
  - 2021 coal-unit upgrading plan;
  - 2022 modern energy-system plan;
  - 2023 coal-fired power capacity-pricing mechanism.
- [ ] Review the GEM citation problem:
  - distinguish the official Global Energy Monitor tracker release from the Zenodo/Modelblocks archive DOI;
  - decide what should be cited in the manuscript and what belongs in data availability or replication notes.
- [ ] Choose 3-5 truly useful supplemental references from `output/energy_policy_lockin_0820/literature_map_50.md`; do not expand the literature just to make the reference list look bigger.

Required Stage 06 structure:

- [ ] A. Overall conclusion
- [ ] B. Data-source gap list
- [ ] C. Data provenance to add in Methods
- [ ] D. In-text citation and reference-list check
- [ ] E. Required primary policy files
- [ ] F. Recommended supplemental literature
- [ ] G. Data availability / replication package risks
- [ ] H. Pre-submission priority ranking

## 2. Locked decisions not to reopen without new evidence

- [ ] Cox main specification is boundary-inclusive end-of-reported-year.
- [ ] Cox main count is 4,326 contributing units / 1,078 modeled retirement events / 12,470 unit-period intervals.
- [ ] Old 4,323 / 952 / 12,344 Cox version is legacy/robustness only.
- [ ] New Figure 2 uses `result/figures/0907_cox_boundary_main/`.
- [ ] Figure 5 main version should use terminal/final-use fields.
- [ ] The old 68.2% -> 58.8% number is a constructed five-energy consumption basket, not final use.
- [ ] Terminal Figure 5 coal share is 44.8436% -> 21.1224%, rounded in text as 44.8% -> 21.1%.
- [ ] Post-2012 Cox p-values above 0.05 are not a formal post-versus-pre equality test.
- [ ] Figure 3 is a three-dimensional descriptive typology, not a full mechanism test or full constraints bundle.

## 3. Files not to modify before explicit authorization

- [ ] Do not overwrite `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`.
- [ ] Do not modify `code/coal_retirement_survival_final_0820.py`.
- [ ] Do not modify `code/plot_energy_policy_evidence_figures_0822.py`.
- [ ] Do not overwrite old Figure 1-5 assets under `result/figures/energy_policy_lockin_0820/`.
- [ ] Do not overwrite old Cox results under `result/tables/0820_coal_retirement_survival_final/`.
- [ ] Do not modify raw GEM, Wind, NEA, append, or source-data folders.
- [ ] Do not modify bibliography files until Stage 06 identifies the exact required changes and the user authorizes them.

## 4. After Stage 06: reproducibility package

- [ ] Create or update a replication README.
- [ ] Create a data dictionary covering manuscript variables, source files, construction scripts, units, coverage, and access restrictions.
- [ ] Add a requirements or environment file for Python dependencies.
- [ ] Document Stata version and external package dependencies.
- [ ] Add a run log or run-order file that distinguishes reproducible steps from proprietary/manual Wind steps.
- [ ] Record which source files cannot be redistributed and how the author should document access.

## 5. After provenance is settled: manuscript revision

Only start after user authorization. Work from a dated copy of the 2026-09-01 DOCX.

- [ ] Create a new DOCX version; do not overwrite the baseline.
- [ ] Replace old Cox counts, HRs, p-values, CIs, event counts, and table notes with the boundary-inclusive version.
- [ ] Insert the new Figure 2 from `result/figures/0907_cox_boundary_main/`.
- [ ] Insert the terminal Figure 5 from `result/figures/0907_figure5_terminal/`.
- [ ] Insert the missing Cox hazard-ratio table.
- [ ] Insert the missing provincial FE/supporting-results table.
- [ ] Update Abstract, Methods, Results, figure notes, table notes, Data availability, declarations, and references.
- [ ] Keep all claims diagnostic/observational where the design does not identify a causal effect.

## 6. Final pre-submission checks

- [ ] Render the revised DOCX to PDF and inspect page layout.
- [ ] Check all embedded figures visually.
- [ ] Confirm table numbering, figure numbering, captions, notes, and cross-references.
- [ ] Confirm references match in-text citations.
- [ ] Confirm data availability, funding, competing interests, AI declaration, title page, highlights, keywords, and any journal-specific requirements.
- [ ] Save a final submission bundle with manuscript, figures, tables, highlights, cover letter if needed, and replication notes.

