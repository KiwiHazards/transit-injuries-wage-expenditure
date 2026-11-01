from pathlib import Path
import pandas as pd,numpy as np,sys,json,hashlib
R=Path(__file__).resolve().parent;O=R/'outputs'
sys.path.insert(0,str(R.parent/'transit_analysis_2026_09_17'))
import analyze as base
base.OUT=O
p=pd.read_csv(O/'operator_panel.csv',dtype={'ntd_id':str})
e=pd.read_csv(R/'raw/major_bus_events.csv',dtype={'_5_digit_ntd_id':str})
e['_5_digit_ntd_id']=e['_5_digit_ntd_id'].str.zfill(5)
assert not e.duplicated(['_5_digit_ntd_id','incident_number']).any()
e['date']=pd.to_datetime(e.incident_date);assert e.date.notna().all()
e['period']=e.date.dt.to_period('M')
e['op']=pd.to_numeric(e.transit_vehicle_operator_1,errors='raise').fillna(0)
e['serious']=pd.to_numeric(e.transit_vehicle_operator_2,errors='raise').fillna(0)
counts=[]
for row in p.itertuples():
 assert row.safety_period_complete and row.operator_injuries_months==12
 counts.append(e.loc[(e._5_digit_ntd_id==row.ntd_id)&e.period.between(pd.Period(row.safety_start_month,'M'),pd.Period(row.safety_end_month,'M')),'op'].sum())
p['major_operator_injuries_fy']=counts
p['major_operator_rate']=1e5*p.major_operator_injuries_fy/p.vehicle_revenue_hours_fy
prior=p[['ntd_id','report_year','major_operator_rate']].copy();prior.report_year+=1;prior=prior.rename(columns={'major_operator_rate':'lag_major_operator_rate'})
p=p.merge(prior,on=['ntd_id','report_year'],validate='one_to_one',how='left')
q=p[p.op_lag_eligible].copy()
c,m,z,*_=base.fit(q,'op_log_real_wage','lag_major_operator_rate',base.CONTROL,('ntd_id','report_year'),check=False)
result=pd.DataFrame([{'model':'M1','label':'Major-event operator injuries only; exploratory diagnostic',**m,**c.iloc[0].to_dict()}]);result.to_csv(O/'major_diagnostic_model.csv',index=False)
c.to_csv(O/'major_diagnostic_coefficients.csv',index=False);z[['ntd_id','report_year']].to_csv(O/'major_diagnostic_membership.csv',index=False)
p[['ntd_id','report_year','major_operator_injuries_fy','major_operator_rate','lag_major_operator_rate']].to_csv(O/'major_operator_panel.csv',index=False)
audit={'records':len(e),'missing_operator_injury_values':int(e.transit_vehicle_operator_1.isna().sum()),'serious_bus_injuries':float(e.serious.sum()),'major_operator_injuries_screened':float(sum(counts)),'plan_sha256':hashlib.sha256((R/'MAJOR_EVENT_CHECK_PLAN.md').read_bytes()).hexdigest()}
(O/'major_diagnostic_audit.json').write_text(json.dumps(audit,indent=2));print(audit);print(result.to_string(index=False))
