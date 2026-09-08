# LaTeX version

This folder contains a LaTeX reconstruction of the 2026-09-08 text-revised manuscript.

Main file:

- `manuscript_text_revised.tex`

Local bibliography files:

- `green_credit_transition_refs.bib`
- `local_refs.bib`

The manuscript links figure PDFs from the repository-level `result/figures/` folder using relative paths. Required links are:

- `../../../../result/figures/energy_policy_lockin_0820/Figure_1_asset_lifecycle.pdf`
- `../../../../result/figures/0907_cox_boundary_main/Figure_2_retirement_evidence_boundary_inclusive.pdf`
- `../../../../result/figures/energy_policy_lockin_0820/Figure_3_constraint_typology.pdf`
- `../../../../result/figures/energy_policy_lockin_0820/Figure_4_case_lifecycles.pdf`
- `../../../../result/figures/0907_figure5_terminal/Figure_5_annual_composition_shares_terminal.pdf`

Build command from this folder:

```bash
latexmk -pdf -interaction=nonstopmode manuscript_text_revised.tex
```

