# Stage 06 addendum for the final LaTeX workflow

Date: 2026-09-11  
Scope: targeted supplement to `06_data_citation_reference_audit.md`; this is not a new provenance or reference audit.

## 1. Additional manuscript files checked

The following files, which were not all available to the original Stage 06 audit, have now been checked directly:

- `output/energy_policy_lockin_0901/Designed_for_Adjustment_2026-09-01.docx`
- `output/energy_policy_lockin_0820/manuscript.docx`
- `output/energy_policy_lockin_0901/manuscript_text_revision_20260908/manuscript_text_revised_2026-09-08.docx`
- `output/energy_policy_lockin_0901/manuscript_text_revision_20260908/latex/manuscript_text_revised.tex`

The 2026-09-01 baseline has SHA-256 `ba955ff5bec7f8ff4d4aa0cf4e4ce74db9a6f43ea4132eadedf5cb1b8dbd314c`. It contains 126 non-empty body paragraphs, seven tables (15 table rows), five inline figures, and one section. The 0820 Word file has the same corresponding counts.

## 2. 0901 baseline versus 0820 source manuscript

The direct Word-body comparison found no substantive empirical, methodological, interpretive, citation, or data-source content present only in the 0901 baseline. The differences are limited to:

1. The 0901 file contains the front-matter line `Anonymous manuscript for review`; the 0820 file does not.
2. The 0901 heading is `Discussion: connecting adjustment to exit`; the 0820 heading is `Discussion`.
3. The 0820 file contains an explicit `References` heading at the body location where the 0901 extraction proceeds directly to the entries.
4. Several figure-note table rows have different merged-cell OOXML structures. Their visible note text is the same; the difference is document structure/formatting, not content.

Accordingly, the fact that the 0908 candidate was generated from the 0820 Word file does **not** imply that substantive content unique to the 0901 baseline was omitted.

## 3. 0908 Word candidate and LaTeX text

The 0908 Word candidate has 128 non-empty body paragraphs, nine tables (25 table rows), five inline figures, and one section. The additional table count is consistent with restoration of the Cox hazard-ratio table and the supporting provincial-results table.

The only relevant 0901/0820 carry-over inconsistencies are non-substantive synchronization items:

- The 0908 Word candidate omits `Anonymous manuscript for review` and uses the short `Discussion` heading.
- The 0908 LaTeX file includes `Anonymous manuscript for review` and uses `Discussion: connecting adjustment to exit`.

For the final LaTeX submission workflow, the LaTeX treatment already preserves the two 0901 presentation choices. No missing 0901-specific substantive passage needs to be restored.

## 4. Effect on the Stage 06 conclusions

The Stage 06 audit remains sufficient as the working data/citation/reference audit for the current revision. Its substantive conclusions are unchanged, including the need for author-supplied primary policy sources, clearer GEM tracker/archive citations, and a data-availability statement aligned with the actual replication package.

One Stage 06 risk can now be closed: the 2026-09-01 baseline is present locally and has been compared directly. The earlier statement that the baseline was unavailable should not be carried forward as an unresolved risk.

No full Stage 06 re-audit is necessary. Policy citations, GEM source details, and the final Data availability wording should be integrated only after the authors provide or approve the relevant sources and disclosure choices.
