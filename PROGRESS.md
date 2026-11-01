# Research progress

Public snapshot: October 31, 2026. Research artifacts through October 16, 2026.

The project began with a question about compensation for workplace safety risk and the role of standardized or union pay. The available administrative records support a narrower question: whether prior reported operator injury intensity is associated with subsequent agency wage expenditure per worked hour.

The September 17 analysis plan preceded the original regressions but followed the source audit. It was an internal plan, not an external preregistration. The October 1 operator extension followed the original results and was written before estimating those operator models. It remains exploratory. The retained plan is in `analysis/transit_analysis_2026_09_17/ANALYSIS_PLAN.md`.

By October 14, the work included a fiscal-year-matched panel, operator-specific hours, safety reconciliation, literature integration, and manuscript v6. The original all-staff coefficient was −0.000149; the operator coefficient was −0.000917. Both intervals include zero. Occupational accounting improves alignment but does not turn expenditure into a negotiated base wage.

On October 16, an AI-performed audit rebuilt the screened panel from archived inputs and re-estimated the models using alternative implementations. Its retained reconciliation reports agreement with the original estimates. A separate static AI review found no verified error in the headline calculations. Neither exercise validates the meaning of every source field or supplies human methodological review. This public release adds a fresh estimation check from the processed panels; it does not claim to have rerun the full raw-data audit.

The later audit changes how the results should be presented. Prior-VRH weighting gives an exploratory operator coefficient of −0.019266 (p = 0.0217), compared with the unweighted null. The sign remains negative when individually omitting the fifteen largest agencies considered, although one leave-one-out p-value exceeds 0.05. Large agencies have more influence under this weighting. The result does not establish an injury effect: staffing pressure, recruitment, overtime, and other omitted changes could affect both sides of the regression. The complete retained follow-up is in `audit/output/weighted_followup.json`.

The audits also disagree about how strongly to interpret some diagnostics. A numerical reliability “upper bound” in an earlier auxiliary calculation uses inconsistent residual spaces and should not be used as an established bound or an attenuation correction. Poisson-based noise and power calibrations require assumptions that are not validated here. Sparse counts and concentrated identifying variation are observable concerns; precise claims about latent-risk reliability are not established by those facts alone.

Monthly injury identities and component bounds demonstrate arithmetic compatibility, not independent verification of occupational allocation. The reporting threshold excludes some forms of harm, and a difference between major-only and combined counts need not itself indicate an error. Reporting heterogeneity should be investigated rather than automatically attributed to either real risk or reporting behavior.

The current contribution is therefore a documented administrative-data analysis with explicit measurement limits. It has not established a hazard premium, an injury-driven wage adjustment, or a collective-bargaining mechanism. A defensible extension needs signed agreements, dated wage schedules, occupational crosswalks, and enough independently timed bargaining episodes. The existing CTA and VTA examples are institutional context, not causal evidence.

Before journal submission, the project still needs qualified human review, a more complete novelty assessment, resolution of the measurement questions, and author declarations. Public circulation as a working draft does not imply journal readiness.
