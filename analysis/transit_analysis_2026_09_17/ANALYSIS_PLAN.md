# Analysis plan, fixed before inspecting regression results

Date: 17 September 2026. Internal analysis plan, not an externally registered preregistration. The prior source audit and sample counts were already known. This document is written before any regression estimates in this project stage.

## Question and interpretation

How is reported operator injury intensity associated with wage expenditure per operating labor hour across U.S. transit agencies directly operating conventional bus services, 2019–2024?

The unit is agency–fiscal year. Compensation covers all operating functions; operator injuries describe the operating environment. This mismatch prevents individual hazard-premium interpretation. We will explicitly label wages as expenditure per labor hour, not a contractual wage. Primary inference is associational.

H1: Higher operator-injury intensity in the previous fiscal year is associated with higher current real wage expenditure per operating labor hour. A positive coefficient is consistent with compensation for risk, but does not identify that mechanism. Two-sided 95% intervals and p-values will be reported; a non-significant result will not be relabeled as evidence of no relationship.

Exploratory question: Is higher previous-year real wage expenditure associated with subsequent operator-injury intensity? Retention and perceived effort–reward balance are possible mechanisms, but neither is measured. This is not a second confirmatory hypothesis. Union moderation is deferred until independent dated measurements exist.

## Sample

Begin with the previously screened 1,670 bus agency-years from 304 agencies (245 complete six-year agencies). Preserve this base. Require an exact consecutive prior report year and nonoverlapping adjacent 12-month fiscal windows for lagged measures; never bridge gaps. Exclude agencies with only one usable observation in a fixed-effects specification. Report resulting counts for every model. Retain observed zero injuries; never replace missing safety values with zero.

## Variables and controls

- Wage outcome: log of operating wage expenditure / operating labor hours, deflated with the average monthly national CPI-U (not seasonally adjusted) over the agency's actual fiscal year, relative to the 2024 calendar-year average.
- Main exposure: previous-year operator injuries per 100,000 vehicle revenue hours. Raw units are primary; log(1 + rate) is a sensitivity specification because the rate can be zero or skewed.
- Core controls: previous-year log service hours, previous-year workforce function shares (vehicle maintenance, facility maintenance, administration; vehicle operations is the omitted share), and log real state private-sector average weekly wage. The latter is a broad labor-market proxy, not a city cost-of-living measure. Fiscal-year alignment will use quarterly wage data if available, with any approximation disclosed. No invented or silently imputed controls.
- Full-time/part-time operating-hour share is added if historical components can be reconciled to the frozen totals. Source acquisition failures or measurement differences will be documented before estimation.
- Agency effects account for stable agency/region attributes; year effects account for common annual shocks. Separate region dummies and common pandemic-year dummies are collinear with these effects and will not be added.
- Current staffing/service controls are not automatically preferred because they could respond to injury or compensation. Lagged controls are used in the primary specification, with the same endogeneity caveat.

## Models and uncertainty

Primary: log(real wage per operating hour) = agency effects + report-year effects + beta × previous-year injury intensity + controls. Equal weight per agency-year. Agency-clustered sandwich standard errors with finite-sample correction and t inference using number of agency clusters minus one degrees of freedom. No lagged dependent wage variable in this short panel; a conventional dynamic fixed-effects model would introduce additional small-T bias.

Report a descriptive same-year association and a parsimonious lagged model without covariates alongside the primary model. Compare adjusted and unadjusted models on the same complete-case sample where feasible.

Exploratory reverse-direction model: log(1 + injury rate) on prior log real wages, agency/year effects, prior service/function controls and the state wage proxy. This outcome transformation is descriptive and its coefficient must not be called an injury-count elasticity. If a Poisson count model is added later, identify it as an exploratory extension and handle all-zero agency groups explicitly.

## Prespecified sensitivity checks

1. Balanced six-year cohort, retaining consecutive lag pairs.
2. Exclude pairs in which either predictor or outcome year is 2020 or 2021.
3. Restrict both years to pre-2023 reporting periods, recognizing the short residual panel.
4. Remove the five largest agencies by average vehicle revenue hours, selected without regression results.
5. Use log(1 + injury rate) instead of the raw rate.
6. Use total employee injuries per 100,000 operating labor hours, which matches the broader compensation workforce more closely but still does not capture every occupational injury.
7. Use total compensation expense including paid absences and benefits, only when source quality and components permit.
8. State-by-year effects as a stronger broad geographic shock adjustment if identifiable; drop the collinear state wage control if appropriate.
9. Nominal wage outcome with year effects as an inflation sensitivity.
10. Inspect unusually large year-to-year wage changes; report a sensitivity excluding changes exceeding 50%, without silently deleting them from the main model.

All specifications will be retained regardless of sign or statistical significance. These checks are diagnostic, not independent confirmations; exploratory multiplicity will be acknowledged. No causal claim follows from lagging or fixed effects.

## Deliverables and gates

Create an augmented panel with documented source joins, descriptive tables, scientific figures, coefficient/sample tables, reproducible code, and draft methods/results. Verify fiscal-year inflation, control coverage, lag adjacency, design rank, and at least one independently calculated coefficient/covariance result. Source definition changes, state proxies, worker mix, reporting behavior and employer boundaries remain limitations to address before submission. Literature and introduction must retain the planned theoretical tension regardless of the fitted signs.
