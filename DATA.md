# Data and release scope

The processed panels are agency-level aggregates assembled from National Transit Database employee, operating-expense, agency-information, and monthly safety/service records for 2019–2024. CPI-U supplies the national inflation adjustment. State private-sector QCEW wages supply a labor-market control. They are not employee-level records.

Primary source portals:

- [FTA National Transit Database](https://www.transit.dot.gov/ntd)
- [BLS CPI data](https://www.bls.gov/cpi/data.htm)
- [BLS QCEW data](https://www.bls.gov/cew/downloadable-data-files.htm)

`analysis/transit_analysis_2026_09_17/outputs/augmented_bus_panel.csv` contains the original screened panel and controls. `analysis/journal_revision/outputs/operator_panel.csv` adds occupational operator hours and the exploratory operator outcome. `audit/output/analysis_panel_with_lags.csv` is the later audit’s reconstruction used for its weighted diagnostics. The archive’s source vintage is preserved in those derived files; a current download may differ.

The screen retains 1,670 agency-years from 304 agencies with usable labor and expense records, complete fiscal-year safety windows, positive service exposure, and the archived quality checks. The one-year models remove singleton agencies and use 1,345 observations from 284 agencies. Missing records are not treated as zero injuries, and missing years are not bridged when forming lags.

This release includes selected preparation code for transparency, but not the raw inputs it requires. Raw NTD workbooks/API extracts, original download archives, copyrighted journal PDFs and full-text extracts, contract originals, private correspondence, and machine-local audit logs are excluded. Published panels permit re-estimation but cannot independently establish raw-to-panel fidelity. The earlier raw-data replication is retained evidence, not a new full-source rerun in this release.

The preparation and estimation scripts copied from the frozen package are unchanged. The new `reproduce.py` runs checks from published panels without overwriting archived outputs. `SHA256SUMS.txt` records public file hashes, excluding itself and Git metadata.
