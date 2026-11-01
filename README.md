# Transit operator injuries and wage expenditure

This project examines whether reported operator injuries are associated with later wage expenditure in U.S. bus agencies. It links National Transit Database records for directly operated conventional bus service from 2019 through 2024, matching safety observations to each agency’s fiscal year.

The screened panel contains 1,670 agency-years from 304 agencies. The main one-year-lag models use 1,345 observations from 284 agencies. The original all-staff analysis and the later operator-specific analysis do not detect the predicted positive annual association. These estimates concern expenditure per worked hour; they cannot establish whether operators receive compensation for occupational risk.

## Results

| Specification | Coefficient | 95% confidence interval |
| --- | ---: | ---: |
| Originally planned all-staff outcome | −0.000149 | −0.008255 to 0.007957 |
| Exploratory operator-specific outcome | −0.000917 | −0.009713 to 0.007879 |

The predictor is prior reported operator injuries per 100,000 vehicle revenue hours. The outcome is log real wage expenditure per worked operating hour. Both models include agency and year effects and the archived controls. Intervals use the original agency-clustered CR1 convention, which counts the agency effects in the finite-sample correction. Alternative conventions change uncertainty modestly without changing these conclusions.

A subsequent exploratory audit found a negative operator association when weighting by prior vehicle revenue hours (coefficient −0.019266, p = 0.0217). Weighting changes the estimand. This result is reported alongside the original estimates, not treated as a confirmatory finding or a causal effect. See [research progress](PROGRESS.md) and the [audit outputs](audit/output).

## Paper and code

The [working paper PDF](paper/working-paper-v6.pdf) preserves manuscript v6 from October 14, 2026. A [text version](paper/working-paper-v6.txt) is also available. The paper predates the October 16 audit findings; read it with [PROGRESS.md](PROGRESS.md). This October 31 public snapshot does not represent a new empirical study or a peer-reviewed publication.

`analysis/` contains the archived preparation and estimation scripts, processed agency panels, model membership, and numerical results. `audit/` contains selected subsequent replication results and the weighted diagnostic code. Preparation scripts require raw inputs retained outside this release; they are included to document the original construction. The public package supports estimation from the published panels, not a complete rebuild from raw source files.

To check the original headline estimates and the weighted diagnostic:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py
```

The check reads the published panels, compares coefficients and uncertainty with the archived results, and writes its report to `reproduced/`. See [data provenance](DATA.md) for scope and exclusions.

## Interpretation

NTD injury reporting covers a defined set of transit events. It does not count every occupational injury, illness, or delayed-treatment case. Wage expenditure per worked hour can change with overtime, workforce composition, progression, and payroll timing even when contractual base rates do not change. Sparse injury counts, reporting differences, and the short panel limit inference. Neither a lag nor fixed effects supplies causal identification, and an interval spanning zero does not establish equivalence or no compensation response.

The next substantive step is to verify occupational reporting and build a source-documented set of contracts and wage schedules before testing bargaining mechanisms. The current data do not contain a verified contract-episode design.

## Use and attribution

Author: Kruthik Ankam, University of Washington Seattle.

The whitepaper PDF and text are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [the paper license](paper/LICENSE.md). This permission covers the whitepaper, not a blanket license for the code or third-party source data. Cite the repository and release tag when referring to this working snapshot. The [Zenodo whitepaper record](https://doi.org/10.5281/zenodo.23850479) provides a persistent citation.

AI tools assisted the analysis, manuscript drafting, and internal audits. Their checks are not independent human peer review. The original plans and the distinction between planned and exploratory work are preserved.
