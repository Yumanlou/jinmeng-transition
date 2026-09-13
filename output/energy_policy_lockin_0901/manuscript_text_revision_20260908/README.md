# Manuscript text revision package, 2026-09-08

This folder contains a text-level revision of the current Word manuscript:

- `manuscript_text_revised_2026-09-08.docx`

The original manuscript was not overwritten. This revised copy was generated from the current `output/energy_policy_lockin_0820/manuscript.docx` version supplied by the author.

## Main text changes

1. Updated the Cox retirement specification from the legacy 4,323 / 952 / 12,344 version to the boundary-inclusive annual-time specification:
   - 4,326 contributing coal units
   - 1,078 modeled retirement events
   - 12,470 unit-period intervals

2. Replaced the main Cox hazard ratios, p values, confidence intervals, event counts, and table note with the locked boundary-inclusive results:
   - 2000-2011: HR 1.299, p=0.035, 95% CI [1.019, 1.657], 446 events
   - 2012-2015: HR 1.117, p=0.542, 95% CI [0.783, 1.594], 165 events
   - 2016-2020: HR 1.127, p=0.573, 95% CI [0.744, 1.708], 327 events
   - 2021-2025: HR 1.110, p=0.622, 95% CI [0.733, 1.681], 140 events

   The Figure 2 note also states the end-of-reported-year annual-time convention used by the main Cox specification.

3. Added the missing Cox hazard-ratio table to the Word manuscript.

4. Added the missing supporting provincial fixed-effect results table:
   - five-energy final intensity
   - final-coal intensity
   - five-energy coal share
   - industrial SO2

5. Corrected Figure 5 text from the old `68.2% -> 58.8%` statement to the terminal/final-use basket statement:
   - coal share in the constructed five-energy terminal/final-use basket fell from `44.8%` in 2006 to `21.1%` in 2022.

6. Clarified that the Figure 5 basket uses terminal-consumption fields for coal, oil products, LPG, natural gas, and electricity. It is not total primary energy or complete total final energy, and electricity is not treated as a clean-energy category.

7. Clarified that Figure 3 displays three descriptive dimensions only:
   - reconstructed coal operating stock
   - renewable-consumption share
   - pre-policy resource-dependence index

   The text now avoids implying that Figure 3 jointly displays or tests the full constraint bundle, including reliability, utilization, curtailment, or project-pipeline constraints.

8. Clarified that the province-year lifecycle regressions use post-2012 x pre-policy thermal-capacity exposure, not the five-energy terminal/final-use coal-share exposure used elsewhere.

9. Corrected the Shanxi-Inner Mongolia source label from government-work-report text to provincial policy-document text.

10. Sharpened the data-availability and GEM reference wording:
    - Wind data are subject to redistribution limits.
    - GEM official tracker releases are distinguished from the Zenodo archive record used for source preservation.

11. Preserved author-confirmation language in the competing-interest, funding, and generative-AI declarations. These statements still require author verification before submission.

## Required figure links

Use the following figure files when linking or replacing images in the manuscript or LaTeX version:

1. Figure 1:
   - `result/figures/energy_policy_lockin_0820/Figure_1_asset_lifecycle.pdf`
   - `result/figures/energy_policy_lockin_0820/Figure_1_asset_lifecycle.png`

2. Figure 2:
   - `result/figures/0907_cox_boundary_main/Figure_2_retirement_evidence_boundary_inclusive.pdf`
   - `result/figures/0907_cox_boundary_main/Figure_2_retirement_evidence_boundary_inclusive.png`

3. Figure 3:
   - `result/figures/energy_policy_lockin_0820/Figure_3_constraint_typology.pdf`
   - `result/figures/energy_policy_lockin_0820/Figure_3_constraint_typology.png`

4. Figure 4:
   - `result/figures/energy_policy_lockin_0820/Figure_4_case_lifecycles.pdf`
   - `result/figures/energy_policy_lockin_0820/Figure_4_case_lifecycles.png`

5. Figure 5:
   - `result/figures/0911_figure5_terminal_layout_fix/Figure_5_annual_composition_shares_terminal_layout_fixed.pdf`
   - `result/figures/0911_figure5_terminal_layout_fix/Figure_5_annual_composition_shares_terminal_layout_fixed.png`

No empirical scripts, source data, old result files, or bibliography source files were modified in this package.

## Verification

The revised DOCX was structurally checked and rendered for layout QA:

- DOCX package test: passed with `unzip -t`.
- Embedded media count: 5 images retained.
- Rendered page count: 21 pages.
- The inserted tables rendered without visible clipping or broken layout.

## LaTeX folder

The `latex/` subfolder contains a LaTeX version constructed from the same text-level revision.
