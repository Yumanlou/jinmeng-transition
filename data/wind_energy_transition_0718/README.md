# Wind energy-transition extraction

Extraction date: 2026-07-18  
Requested panel window: 2000-2023  
Panel key: `province` x `year` (31 provinces, 744 rows)

## Current status

The first extraction run discovered 295 Wind EDB series and downloaded 24,534
raw observations. Wind returned `QUOTA_ERROR` for the final four fetch batches,
so the files are usable as an audited partial extraction but are not yet a
complete replacement for the project's existing Wind/yearbook variables.

## Files

- `wind_energy_transition_raw_long.csv`: all observations returned by Wind.
- `wind_generation_panel_2000_2023.csv`: NBS monthly YTD generation, using
  December observations and converting to billion kWh.
- `wind_capacity_additions_panel_2000_2023.csv`: wind/solar capacity and direct
  additions, plus additions calculated from stock differences.
- `wind_energy_flows_panel_2000_2023.csv`: coal/electricity transfers in and
  out. Raw outflow values and absolute-value versions are both retained.
- `wind_energy_transition_panel_2000_2023.csv`: combined province-year panel.
- `wind_energy_transition_codebook.csv`: Wind code, source, unit, frequency,
  annualization method, and update date.
- `wind_energy_transition_coverage.csv`: coverage by variable.
- `wind_energy_transition_qa_flags.csv`: extreme year-to-year changes.
- `wind_energy_transition_failures.csv`: missing searches and quota-blocked
  fetch batches.
- `cache/`: raw Wind CLI responses used for reproducibility and resumption.

## Important measurement boundary

Variables prefixed with `nbs_` are National Bureau of Statistics monthly YTD
series. They are not identical to annual totals from the China Energy
Statistical Yearbook. For example, the new NBS wind series returns 40.83
billion kWh for Shanxi in 2022, while the existing project yearbook series is
46.642 billion kWh. These variables must therefore be treated as alternative
NBS measures and must not overwrite the existing yearbook series.

## Flow QA

Wind's energy-balance outflow series contains mixed signs. Both the returned
raw value and an absolute-value version are retained. The Inner Mongolia 2013
electricity outflow value is also flagged as an extreme jump and must be
checked against the original yearbook before regression use.

## Resume command

After the Wind quota is available again, run:

```bash
python3 code/fetch_wind_energy_transition_0718.py \
  --start-year 2000 --end-year 2023 --workers 6 --batch-size 20
```

The script reuses completed caches, performs exact per-province searches for
still-missing capacity and transfer indicators, and fetches only unresolved
batches.
