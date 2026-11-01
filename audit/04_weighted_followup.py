"""Follow-up on pre-listed diagnostic G3 (prior-VRH-weighted O1). Exploratory: checks whether the weighted
estimate is driven by individual large agencies (leave-one-out over the 15 largest) and reports the weighted
P1 (all-staff) analogue and weighted same-year analogue. Reported in full regardless of sign/p."""
import importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd
spec = importlib.util.spec_from_file_location('d', Path(__file__).with_name('03_diagnostics_lib.py'))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
OUT = Path(__file__).resolve().parent / 'output'
s = pd.read_csv(OUT / 'analysis_panel_with_lags.csv', dtype={'ntd_id': str}, parse_dates=['fy_end'])
C = ['lag_log_vrh', 'lag_vehicle_maintenance_share', 'lag_facility_maintenance_share', 'lag_general_administration_share', 'lag_parttime_share', 'log_real_state_wage']
cc = s[s.exact_lag].dropna(subset=['log_real_wage', 'lag_inj_rate'] + C).copy()
cc['w_prior_vrh'] = cc.lag_vehicle_revenue_hours_fy
out = {}
for nm, y in [('O1_weighted', 'log_real_op_wage'), ('P1_weighted', 'log_real_wage')]:
    r = d.fe_ols(cc, y, ['lag_inj_rate'] + C, w='w_prior_vrh')
    out[nm] = {'b': r['b'], 'se': r['se'], 'p': r['p'], 'N': r['N']}
r = d.fe_ols(cc, 'log_real_op_wage', ['inj_rate'] + C, w='w_prior_vrh')
out['O1_weighted_same_year_rate'] = {'b': r['b'], 'se': r['se'], 'p': r['p']}
big = s.groupby('ntd_id').vehicle_revenue_hours_fy.mean().nlargest(15)
names = s.groupby('ntd_id').agency.last()
loo = []
for a in big.index:
    r = d.fe_ols(cc[cc.ntd_id != a], 'log_real_op_wage', ['lag_inj_rate'] + C, w='w_prior_vrh')
    loo.append({'dropped': a, 'agency': names[a], 'mean_vrh': float(big[a]), 'b': r['b'], 'p': r['p']})
out['O1_weighted_LOO_15_largest'] = loo
# weight share of the largest agencies
wsh = cc.groupby('ntd_id').w_prior_vrh.sum() / cc.w_prior_vrh.sum()
out['weight_share_top5'] = float(wsh.nlargest(5).sum()); out['weight_share_top1'] = {names[wsh.idxmax()]: float(wsh.max())}
(OUT / 'weighted_followup.json').write_text(json.dumps(out, indent=1, default=float))
print(json.dumps(out, indent=1, default=float))
