from pathlib import Path
import pandas as pd, numpy as np,json,hashlib
R=Path(__file__).resolve().parent;O=R/'outputs';O.mkdir(exist_ok=True)
p=pd.read_csv(R.parent/'transit_analysis_2026_09_17/outputs/augmented_bus_panel.csv',dtype={'ntd_id':str})
parts=[];audit=[]
for y in range(2019,2025):
 f=R/f'raw/operators_{y}.xlsx' if y<2024 else R.parent/'national_transit_audit/raw/employees_raw_2024.xlsx'
 d=pd.read_excel(f,dtype={'NTD ID':str});d['ntd_id']=d['NTD ID'].str.replace(r'\.0$','',regex=True).str.zfill(5)
 d=d[d.Mode.eq('MB')&d.TOS.eq('DO')].copy();assert not d.ntd_id.duplicated().any()
 d['report_year']=y
 for label,kind in [('operator','Operator'),('nonoperator','Non-Operator')]:
  cs=[f'Total {typ} {kind} (Operating Labor) Hours Worked' for typ in ['Full Time','Part Time']]
  d[label+'_hours']=d[cs].sum(axis=1,min_count=2)
  for typ in ['Full Time','Part Time']:
   fs=[f'{typ} {kind} ({fn}) Hours Worked' for fn in ['Vehicle Operations','Vehicle Maintenance','Facility Maintenance','General Administration']]
   err=d[fs].sum(axis=1,min_count=4)-d[f'Total {typ} {kind} (Operating Labor) Hours Worked']
   audit.append({'year':y,'type':typ,'kind':kind,'rows':len(d),'missing_components':int(d[fs].isna().any(axis=1).sum()),'max_identity_error':float(err.abs().max())})
   assert err.dropna().abs().le(.01).all()
 parts.append(d[['ntd_id','report_year','operator_hours','nonoperator_hours']])
r=pd.concat(parts);p=p.merge(r,on=['ntd_id','report_year'],how='left',validate='one_to_one',indicator='operator_source_join')
p['raw_hour_difference']=p.operator_hours+p.nonoperator_hours-p.operating_hours
p['op_nominal_wage']=p.operators_wages/p.operator_hours.where(p.operator_hours.gt(0))
p['op_real_wage']=p.op_nominal_wage*p.real_wage_per_hour/p.wage_expense_per_operating_hour
p['op_valid']=p.operator_source_join.eq('both')&p.raw_hour_difference.abs().le(.01)&p.operator_hours.gt(0)&p.nonoperator_hours.ge(0)&p.operators_wages.gt(0)&p.op_nominal_wage.between(7.25,150)
p['op_log_real_wage']=np.log(p.op_real_wage.where(p.op_valid))
p['op_injury_labor_rate']=1e5*p.operator_injuries_fy/p.operator_hours.where(p.op_valid)
prev=p[['ntd_id','report_year','op_valid','op_real_wage','op_injury_labor_rate']].copy();prev.report_year+=1;prev=prev.rename(columns={c:'lag_'+c for c in prev if c not in ['ntd_id','report_year']})
p=p.merge(prev,on=['ntd_id','report_year'],how='left',validate='one_to_one');p['op_lag_eligible']=p.exact_lag_pair&p.op_valid&p.lag_op_valid.eq(True)
p['op_large_wage_change']=(p.op_real_wage/p.lag_op_real_wage-1).abs().gt(.5)
p.to_csv(O/'operator_panel.csv',index=False)
p[~p.op_valid].to_csv(O/'operator_exclusions.csv',index=False)
pd.DataFrame(audit).to_csv(O/'operator_raw_identities.csv',index=False)
yr=p.groupby('report_year').agg(rows=('ntd_id','size'),valid=('op_valid','sum'),max_raw_hour_difference=('raw_hour_difference',lambda s:s.abs().max()),median_operator_nominal=('op_nominal_wage','median'),median_all_nominal=('wage_expense_per_operating_hour','median')).reset_index();yr.to_csv(O/'operator_annual_audit.csv',index=False)
summary={'base_rows':len(p),'matched':int(p.operator_source_join.eq('both').sum()),'valid':int(p.op_valid.sum()),'lag_eligible':int(p.op_lag_eligible.sum()),'maximum_raw_summary_difference':float(p.raw_hour_difference.abs().max()),'extension_plan_sha256':hashlib.sha256((R/'EXTENSION_PLAN.md').read_bytes()).hexdigest()}
(O/'operator_preparation_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(yr.to_string(index=False))
