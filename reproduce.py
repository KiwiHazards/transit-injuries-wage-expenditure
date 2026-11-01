"""Re-estimate headline associations from public panels without changing archives."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def main():
    original_dir = ROOT / "analysis/transit_analysis_2026_09_17"
    original = module("original", original_dir / "analyze.py")
    out = ROOT / "reproduced"
    out.mkdir(exist_ok=True)
    original.OUT = out
    panel = pd.read_csv(ROOT / "analysis/journal_revision/outputs/operator_panel.csv", dtype={"ntd_id": str})
    archived = pd.read_csv(ROOT / "analysis/journal_revision/outputs/operator_models.csv").set_index("model")
    sample = panel[panel.op_lag_eligible].copy()
    results = {}
    for name, outcome in [("C1", "log_real_wage"), ("O1", "op_log_real_wage")]:
        coefs, meta, *_ = original.fit(sample, outcome, "lag_injury_rate", original.CONTROL, check=True)
        row = coefs.iloc[0]
        for key in ["estimate", "cluster_se", "ci_low", "ci_high", "p_two_sided"]:
            np.testing.assert_allclose(row[key], archived.loc[name, key], rtol=1e-7, atol=1e-9)
        assert meta["n"] == 1345 and meta["agencies"] == 284
        results[name] = {"estimate": float(row.estimate), "cluster_se": float(row.cluster_se), "n": meta["n"], "agencies": meta["agencies"]}
    diagnostic = module("diagnostic", ROOT / "audit/03_diagnostics_lib.py")
    s = pd.read_csv(ROOT / "audit/output/analysis_panel_with_lags.csv", dtype={"ntd_id": str})
    controls = ["lag_log_vrh", "lag_vehicle_maintenance_share", "lag_facility_maintenance_share", "lag_general_administration_share", "lag_parttime_share", "log_real_state_wage"]
    s = s[s.exact_lag].dropna(subset=["log_real_wage", "lag_inj_rate", *controls]).copy()
    s["w_prior_vrh"] = s.lag_vehicle_revenue_hours_fy
    weighted = diagnostic.fe_ols(s, "log_real_op_wage", ["lag_inj_rate", *controls], w="w_prior_vrh")
    target = json.loads((ROOT / "audit/output/weighted_followup.json").read_text())["O1_weighted"]
    for key in ["b", "se", "p", "N"]:
        np.testing.assert_allclose(weighted[key], target[key], rtol=1e-7, atol=1e-9)
    results["O1_weighted"] = {key: float(weighted[key]) for key in ["b", "se", "p", "N"]}
    results["scope"] = "Estimation from released processed panels; no raw-source rebuild."
    (out / "verification.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
