from pathlib import Path
import sys,json,numpy as np,pandas as pd
R=Path(__file__).resolve().parent;O=R/'outputs'
sys.path.insert(0,str(R.parent/'transit_analysis_2026_09_17'))
import analyze as original
original.OUT=O
p=pd.read_csv(O/'operator_panel.csv',dtype={'ntd_id':str});p['fy_end_date']=pd.to_datetime(p.fy_end_date)
q=p[p.op_lag_eligible].copy();C=original.CONTROL
specs=[('O1','Operator outcome; service-hour injury rate',q,'op_log_real_wage','lag_injury_rate',C,('ntd_id','report_year')),
('C1','All-staff outcome; same observations',q,'log_real_wage','lag_injury_rate',C,('ntd_id','report_year')),
('O2','Operator outcome; operator-hour injury rate',q,'op_log_real_wage','lag_op_injury_labor_rate',C,('ntd_id','report_year')),
('O3','Balanced cohort',q[q.balanced_six_years],'op_log_real_wage','lag_injury_rate',C,('ntd_id','report_year')),
('O4','Neither year in 2020 or 2021',q[~q.report_year.isin([2020,2021,2022])],'op_log_real_wage','lag_injury_rate',C,('ntd_id','report_year')),
('O5','Fiscal windows end before 2023',q[q.fy_end_date.lt('2023-01-01')],'op_log_real_wage','lag_injury_rate',C,('ntd_id','report_year')),
('O6','State by year effects',q,'op_log_real_wage','lag_injury_rate',C[:-1],('ntd_id','state_year')),
('O7','Log one plus injury rate',q,'op_log_real_wage','lag_log1p_injury_rate',C,('ntd_id','report_year')),
('O8','Exclude operator wage changes over 50 percent',q[~q.op_large_wage_change],'op_log_real_wage','lag_injury_rate',C,('ntd_id','report_year'))]
rows=[];membership=[];coefs=[]
for mid,label,d,y,x,cs,fe in specs:
 c,m,z,*_=original.fit(d,y,x,cs,fe,check=mid=='O1')
 rows.append({'model':mid,'label':label,'outcome':y,'predictor':x,**m,**c.iloc[0].to_dict()})
 membership.append(z[['ntd_id','report_year']].assign(model=mid));coefs.append(c.assign(model=mid))
out=pd.DataFrame(rows);out.to_csv(O/'operator_models.csv',index=False);pd.concat(membership).to_csv(O/'operator_model_membership.csv',index=False);pd.concat(coefs).to_csv(O/'operator_all_coefficients.csv',index=False)
assert membership[0][['ntd_id','report_year']].equals(membership[1][['ntd_id','report_year']])
old=pd.read_csv(R.parent/'transit_analysis_2026_09_17/outputs/model_results.csv');target=old[old.model.eq('P1')].iloc[0];new=out[out.model.eq('C1')].iloc[0]
assert abs(target.estimate-new.estimate)<1e-9
print(out[['model','n','agencies','estimate','cluster_se','ci_low','ci_high','p_two_sided']].to_string(index=False))
