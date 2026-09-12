# PR #1 targeted blocker resolution

Date: 2026-09-11  
Branch reviewed: `handoff-energy-policy-20260907`  
Starting PR HEAD: `a87add75975fc0247dbfc57dca2a3ddc70f39067`

This stage follows the team lead's narrowed instructions. It does not reopen the locked Cox specification or Figure 5 variable choice, and it does not revise Data availability, policy/GEM citations, the manuscript text, data, old assets, or model results.

## A. Issues downgraded under the team lead's instruction

The following items identified in `07_pr1_merge_readiness_review.md` are no longer treated as blockers for this targeted PR pass:

1. **DOCX `lastModifiedBy`:** the final submission will be LaTeX, so Word metadata is not a current merge blocker.
2. **Data availability:** the authors will revise this manually; it was not changed here.
3. **Primary policy and GEM citations:** these will be integrated after the authors provide or approve the source records; they were not changed here.
4. **Final journal template and language review:** both are deferred to the final LaTeX stage.
5. **0820 source versus 0901 baseline:** this required a targeted read-only comparison, not reconstruction of the revision from scratch. The comparison below finds no substantive 0901-only material missing from the 0908 candidate.
6. **Stage 06 scope:** only a short baseline/LaTeX addendum was needed. The full provenance audit was not repeated.

The locked empirical decisions remain unchanged: boundary-inclusive Cox is the main specification; the legacy `4,323 / 952 / 12,344` version is robustness/legacy only; Figure 5 uses terminal/final-use fields and the `44.8436% -> 21.1224%` coal-share endpoints.

## B. Figure 5 layout repair and LaTeX path update

### B.1 New figure assets

The layout-fixed terminal/final-use Figure 5 is available at:

- `result/figures/0911_figure5_terminal_layout_fix/Figure_5_annual_composition_shares_terminal_layout_fixed.png`
- `result/figures/0911_figure5_terminal_layout_fix/Figure_5_annual_composition_shares_terminal_layout_fixed.pdf`

The visual repair is limited to canvas and spacing changes:

- increased the left margin and total figure height;
- increased vertical separation between panels;
- wrapped each long vertical-axis label onto two lines;
- added safe exterior padding around axes and legends;
- retained the 0907 colors, panel definitions, titles, legends, year ticks, and 0--100% scales.

Visual inspection of the new PNG confirms that the three vertical-axis labels no longer overlap one another, the left edge is no longer clipped, and the panel titles and legends have adequate separation. The new PDF is a one-page vector figure with a page size of approximately 8.25 by 7.57 inches.

### B.2 Data-consistency evidence

The new figure uses the audited 0907 terminal tables as its sole plotting input. The corresponding verification assets are:

- `result/tables/0911_figure5_terminal_layout_fix/Figure_5_panel_a_terminal_audit.csv`
- `result/tables/0911_figure5_terminal_layout_fix/Figure_5_panels_bc_audit.csv`
- `result/tables/0911_figure5_terminal_layout_fix/Figure_5_terminal_layout_fix_data_consistency.csv`
- `result/tables/0911_figure5_terminal_layout_fix/Figure_5_terminal_layout_fix_metadata.json`

| Check | Panel (a) | Panels (b)--(c) |
|---|---:|---:|
| Rows | 17 | 18 |
| Byte-identical to the 0907 audit CSV | Yes | Yes |
| Maximum absolute numeric difference | 0 | 0 |

Panel (a) therefore remains the constructed five-energy terminal/final-use basket. The coal share is unchanged at **44.8436359121% in 2006** and **21.1224008626% in 2022**. Each of the five terminal fields still has 30 nonmissing provinces in every year from 2006 through 2022.

### B.3 LaTeX replacement

Only one tracked manuscript line was changed, in:

`output/energy_policy_lockin_0901/manuscript_text_revision_20260908/latex/manuscript_text_revised.tex`

The Figure 5 `\includegraphics` path now points to:

`../../../../result/figures/0911_figure5_terminal_layout_fix/Figure_5_annual_composition_shares_terminal_layout_fixed.pdf`

The scoped Git diff confirms that this is the only tracked-file change and that no surrounding caption, note,正文, Figure 2 path, table, Cox result, or Data availability text changed.

The current environment has no `latexmk`, `pdflatex`, `xelatex`, `lualatex`, or `tectonic` executable. Therefore **the existing `manuscript_text_revised.pdf` was not rebuilt and remains unchanged**. The updated LaTeX must be recompiled and visually checked in a working LaTeX environment or the final Energy Policy template environment. The package's `latex/README.md` still lists the old 0907 Figure 5 link because the present authorization allowed modification only of the `.tex` path; this documentation-only line can be synchronized during final package preparation.

## C. 0901, 0820, and 0908 manuscript comparison

### C.1 File-level evidence

| File | Non-empty body paragraphs | Tables / rows | Inline figures | Interpretation |
|---|---:|---:|---:|---|
| `Designed_for_Adjustment_2026-09-01.docx` | 126 | 7 / 15 | 5 | 0901 baseline |
| `output/energy_policy_lockin_0820/manuscript.docx` | 126 | 7 / 15 | 5 | Source used for the 0908 Word revision |
| `manuscript_text_revised_2026-09-08.docx` | 128 | 9 / 25 | 5 | Candidate revision; two core result tables restored |

The SHA-256 values used for this check were:

- 0901 baseline: `ba955ff5bec7f8ff4d4aa0cf4e4ce74db9a6f43ea4132eadedf5cb1b8dbd314c`
- 0820 Word manuscript: `2331366240b0d1309f9f7eec000b5a01ed6b83d89abc70874b11ff41bdb14d4d`
- 0908 candidate Word manuscript: `1e9e4c9646148c6f0b83df7d333daae026f5094c35f881bdb026974f442eb772`

### C.2 Targeted difference table

| Difference | 0901 baseline | 0820 source | 0908 Word candidate | 0908 LaTeX | Substantive omission? |
|---|---|---|---|---|---|
| Anonymous-review line | Present | Absent | Absent | Present | No; front matter only, and final LaTeX preserves it |
| Discussion heading | `Discussion: connecting adjustment to exit` | `Discussion` | `Discussion` | `Discussion: connecting adjustment to exit` | No; heading only, and final LaTeX preserves the 0901 form |
| References heading | Not a separate extracted body paragraph | Present | Present | Bibliography generated by LaTeX commands | No; reference content is not missing |
| Figure-note table-cell structure | Some notes stored in differently merged OOXML cells | Different merge structure | Revised package structure | Native LaTeX notes | No; visible note text is the same in the 0901/0820 comparison |
| Empirical, methods, interpretation, citation, or data-source content unique to 0901 | None found | -- | No 0901-only substantive passage to restore | No 0901-only substantive passage to restore | **No** |

**Conclusion:** the 0901 and 0820 Word files differ only in front matter, a section heading, the explicit References heading, and non-substantive table-cell formatting. The 0908 candidate's derivation from the 0820 Word file did not omit substantive content unique to the 0901 baseline. Rebuilding the entire revision from 0901 is not warranted on this evidence.

The remaining Word-versus-LaTeX differences are presentation synchronization issues, not evidence omissions. Because the team has selected LaTeX for final submission, the LaTeX treatment is the relevant one for the next stage.

## D. Stage 06 addendum decision

A short addendum was necessary because the original Stage 06 report explicitly treated the unavailable 0901 baseline as a residual risk. The new file is:

`output/energy_policy_lockin_0901/06_addendum_for_final_latex_20260911.md`

The addendum records the direct comparison of the 0901 baseline, 0820 source, 0908 Word candidate, and 0908 LaTeX text. It closes the narrow “0901 baseline unavailable” risk and confirms that no substantive 0901-only content was omitted.

The remainder of `06_data_citation_reference_audit.md` is sufficient to support the current revision workflow. Its conclusions on data provenance, primary policy sources, GEM citation structure, proprietary Wind data, and replication materials remain valid but await author choices or source materials. A new full Stage 06 audit is not necessary.

## E. Items still requiring author or final-stage handling

1. **Data availability:** the authors will align the statement with the replication materials and redistribution limits.
2. **Policy and GEM sources:** the authors must provide or approve the primary policy documents and exact GEM tracker/archive citations before Codex integrates them.
3. **LaTeX rebuild:** compile the updated `.tex` in a usable LaTeX or Energy Policy template environment and inspect Figure 5, captions, tables, page breaks, and bibliography output. The current committed PDF is stale with respect to the new Figure 5 path.
4. **Final journal template:** transfer the reviewed text and assets into the required Energy Policy/Elsevier LaTeX format and then run a submission-format check.
5. **Manual language review:** authors should complete the final human language, tone, disclosure, and AI-use review.
6. **Package note synchronization:** update the Figure 5 link listed in `latex/README.md` when broader package-documentation edits are authorized.

None of these deferred items changes the locked Cox results or the terminal/final-use Figure 5 definition.

## F. Current merge recommendation

The substantive targeted blockers from the prior review are now resolved in the working tree:

- Figure 5 has a readable layout with verified zero data difference;
- the LaTeX source points to the corrected Figure 5;
- the 0901/0820 comparison shows no substantive baseline omission;
- Stage 06 has the required short addendum rather than a duplicated audit.

However, these changes are currently working-tree changes and new files; PR #1 at remote HEAD `a87add7` does not contain them until they are committed and pushed. **Therefore, do not merge PR #1 yet in its present remote state.**

Once the new Figure 5 assets, consistency metadata, Stage 06 addendum, Stage 08 report, and one-line LaTeX path change are committed and pushed to the PR branch, the narrowed technical blockers no longer justify withholding merge. At that point the PR can be merged as an **intermediate reviewed revision/handoff package**, with the explicit understanding that it is not yet the final submission package and that the LaTeX PDF still requires recompilation and final-template verification.

No locked Cox or Figure 5 definition question should be reopened unless genuinely new evidence appears.
