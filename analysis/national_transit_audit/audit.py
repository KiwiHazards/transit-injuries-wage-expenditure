"""National NTD linkage feasibility audit. No hypothesis tests or causal estimates.
Requires pandas/numpy and an Excel reader. Sources remain untouched.
"""
from pathlib import Path
import pandas as pd,numpy as np,re,json
ROOT=Path(__file__).resolve().parent;RAW=ROOT/'raw';OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
K=['ntd_id','report_year','mode','type_of_service']
H=['vehicle_operations_hours','vehicle_maintenance_hours','facility_maintenance_hours','general_administration_hours']
PAY=['operators_wages','other_salaries_wages','operator_paid_absences','other_paid_absences','fringe_benefits']
S=['vehicle_revenue_hours','vehicle_revenue_miles','ridership','operator_injuries','other_employee_injuries','total_employee_injuries','operator_fatalities','total_employee_fatalities','total_assaults_on_transit_workers','major_physical_assaults_on_operators','non_major_physical_assaults_on_operators']
def save(d,n):d.to_csv(OUT/n,index=False,float_format='%.8f')
def nid(x):
 s=str(x).strip()
 return str(int(float(s))).zfill(5) if re.fullmatch(r'\d+(?:\.0)?',s) else None
def col(x):return re.sub(r'[^a-z0-9]+','_',str(x).lower().replace('&','')).strip('_')
def xl(file,sheet=0):
 d=pd.read_excel(RAW/file,sheet_name=sheet);d.columns=[col(c) for c in d.columns]
 return d.rename(columns={'tos':'type_of_service','operators_paid_absences':'operator_paid_absences'})
def anyflag(d,cols):return d[cols].fillna('').astype(str).apply(lambda s:s.str.strip().ne('')).any(axis=1)
e_parts=[];x_parts=[];load_audit=[]
for year in [2019,2020,2021]:
 e=xl(f'employees_{year}.xlsx','All Employees by Mode');n0=len(e);e['ntd_id']=e.ntd_id.map(nid);e=e[e.ntd_id.notna()].copy();e['report_year']=year
 e['hours_flagged']=anyflag(e,[h+'_questionable' for h in H]);e['emp_source']='annual_excel_all_employees'
 e_parts.append(e[K+H+['agency','state','total_hours','capital_labor_hours','total_employee_count','hours_flagged','emp_source','total_operating_salary_expenses','total_operating_average_hourly_wage']])
 x=xl(f'expenses_{year}.xlsx','Operating Expenses by Type');x['ntd_id']=x.ntd_id.map(nid);x=x[x.ntd_id.notna()].copy();x['report_year']=year
 x['wages_flagged']=anyflag(x,['operators_wages_questionable','other_salaries_wages_questionable'])
 x['benefit_flagged']=anyflag(x,['operators_paid_absences_questionable','other_paid_absences_questionable','fringe_benefits_questionable'])
 x_parts.append(x[K+PAY+['wages_flagged','benefit_flagged']])
 load_audit.append({'source':'employees_excel','year':year,'source_rows':n0,'retained_numeric_id_rows':len(e)})
er=pd.read_csv(RAW/'employees_2022_2024.csv',dtype={'ntd_id':str});er.ntd_id=er.ntd_id.map(nid)
assert not er.duplicated(K+['full_or_part_time']).any()
assert er.groupby(K).size().eq(2).all()
er['hours_flagged']=anyflag(er,[h+'_q' for h in H]);er['emp_source']='api_full_plus_part_time'
e=er.groupby(K).agg({**{h:lambda s:s.sum(min_count=2) for h in H+['total_hours','capital_labor_hours','total_employee_count']},'agency':'first','state':'first','hours_flagged':'any','emp_source':'first'}).reset_index()
# Resolve 2024 API nulls against the original R-10 workbook, never by blanket fill.
r24=pd.read_excel(RAW/'employees_raw_2024.xlsx').rename(columns={'NTD ID':'ntd_id','Mode':'mode','TOS':'type_of_service'})
r24.ntd_id=r24.ntd_id.map(nid)
checks=[]
fields={**dict(zip(H,['Vehicle Operations','Vehicle Maintenance','Facility Maintenance','General Administration'])),'capital_labor_hours':'Capital Labor'}
for typ in ['Full Time','Part Time']:
 z=er[er.report_year.eq(2024)&er.full_or_part_time.eq(typ)].merge(r24.drop(columns=H+['capital_labor_hours','total_hours','total_employee_count'],errors='ignore'),on=['ntd_id','mode','type_of_service'],validate='one_to_one')
 for field in H+['capital_labor_hours','total_hours','total_employee_count']:
  rawcol=f'Total {typ} ({fields[field]}) Hours Worked' if field in fields else f'Total {typ} '+('Hours Worked' if field=='total_hours' else 'Employee Count')
  mismatch=z[field].notna() & (z[field]-z[rawcol]).abs().gt(.01)
  assert not mismatch.any() and z[rawcol].notna().all()
  checks.append({'employment_type':typ,'field':field,'matched_rows':len(z),'nonnull_disagreements':int(mismatch.sum()),'api_missing':int(z[field].isna().sum()),'missing_api_nonzero_raw':int((z[field].isna()&z[rawcol].ne(0)).sum())})
  vals=z.set_index(['ntd_id','mode','type_of_service'])[rawcol]
  if typ=='Full Time':r24[field]=r24.set_index(['ntd_id','mode','type_of_service']).index.map(vals)
  else:r24[field]+=r24.set_index(['ntd_id','mode','type_of_service']).index.map(vals)
for field in H+['capital_labor_hours','total_hours','total_employee_count']:
 vals=r24.set_index(['ntd_id','mode','type_of_service'])[field]
 mask=e.report_year.eq(2024)
 e.loc[mask,field]=e.loc[mask].set_index(['ntd_id','mode','type_of_service']).index.map(vals)
e.loc[e.report_year.eq(2024),'emp_source']='raw_2024_R10_verified_against_API'
save(pd.DataFrame(checks),'raw_2024_api_reconciliation.csv')
e_parts.append(e)
x=pd.read_csv(RAW/'expenses_2022_2024.csv',dtype={'ntd_id':str});x.ntd_id=x.ntd_id.map(nid)
x['wages_flagged']=anyflag(x,['operators_wages_questionable','other_salaries_wages_1'])
x['benefit_flagged']=anyflag(x,['operator_paid_absences_1','other_paid_absences_1','fringe_benefits_questionable'])
x_parts.append(x[K+PAY+['wages_flagged','benefit_flagged']])
e=pd.concat(e_parts,ignore_index=True);x=pd.concat(x_parts,ignore_index=True)
assert not e.duplicated(K).any()
expense_duplicates=x.duplicated(K,keep=False)
save(x[expense_duplicates],'expense_duplicate_keys.csv')
# Reject ambiguous source keys rather than double count or select arbitrarily.
x=x[~expense_duplicates & x.ntd_id.notna()].copy()
assert not x.duplicated(K).any()
save(e,'employees_harmonized.csv');save(x,'expenses_harmonized.csv')
p=e.merge(x,on=K,how='left',validate='one_to_one',indicator='expense_join')
p['operating_hours']=p[H].sum(axis=1,min_count=4)
p['operating_wages']=p[['operators_wages','other_salaries_wages']].sum(axis=1,min_count=2)
p['cash_and_benefits']=p[PAY].sum(axis=1,min_count=5)
p['wage_expense_per_operating_hour']=p.operating_wages/p.operating_hours.replace(0,np.nan)
p['compensation_expense_per_operating_hour']=p.cash_and_benefits/p.operating_hours.replace(0,np.nan)
p['hours_identity_error']=p.total_hours-p.capital_labor_hours-p.operating_hours
p['legacy_salary_identity_error']=p.total_operating_salary_expenses-p.operating_wages
p['legacy_published_wage_denominator_error']=p.total_operating_salary_expenses/p.total_hours.replace(0,np.nan)-p.total_operating_average_hourly_wage
p['labor_numeric_valid']=p[H+['operators_wages','other_salaries_wages']].notna().all(axis=1)&p[H+['operators_wages','other_salaries_wages']].ge(0).all(axis=1)&p.operating_hours.gt(0)&p.operating_wages.gt(0)&p.hours_identity_error.abs().le(.01)
p['labor_quality_clear']=~p.hours_flagged & ~p.wages_flagged.fillna(True)
p['wage_ratio_review_flag']=p.wage_expense_per_operating_hour.lt(7.25)|p.wage_expense_per_operating_hour.gt(150)
# These broad diagnostic cutoffs are NOT estimates of applicable minimum wage.
fy_parts=[]
for year in range(2019,2025):
 a=xl(f'agency_info_{year}.xlsx');a.ntd_id=a.ntd_id.map(nid);a=a[a.ntd_id.notna()].copy();a['report_year']=year;a['fy_end_date']=pd.to_datetime(a.fy_end_date)
 g=a.groupby(['ntd_id','report_year']).agg(fy_end_date=('fy_end_date','first'),fy_date_count=('fy_end_date','nunique'),info_rows=('fy_end_date','size')).reset_index()
 g.loc[g.fy_date_count.ne(1),'fy_end_date']=pd.NaT
 fy_parts.append(g)
fy=pd.concat(fy_parts,ignore_index=True).sort_values(['ntd_id','report_year'])
fy['previous_fy_end']=fy.groupby('ntd_id').fy_end_date.shift()
fy['previous_report_year']=fy.groupby('ntd_id').report_year.shift()
fy['fy_end_month_changed']=fy.previous_report_year.eq(fy.report_year-1)&fy.fy_end_date.dt.month.ne(fy.previous_fy_end.dt.month)
fy['fy_is_month_end']=fy.fy_end_date.dt.is_month_end
save(fy,'fiscal_year_audit.csv')
p=p.merge(fy,on=['ntd_id','report_year'],how='left',validate='many_to_one')
m=pd.read_csv(RAW/'monthly_2018_2024.csv',dtype={'_5_digit_ntd_id':str},low_memory=False).rename(columns={'_5_digit_ntd_id':'ntd_id'});m.ntd_id=m.ntd_id.map(nid);m['period']=pd.to_datetime(m.month_year).dt.to_period('M')
MK=['ntd_id','mode','type_of_service','period']
m['duplicate_key']=m.duplicated(MK,keep=False)
save(m[m.duplicate_key].drop(columns='period'),'monthly_duplicate_keys.csv')
lookup={key:g for key,g in m.groupby(['ntd_id','mode','type_of_service'])}
annual=[]
for _,r in p.iterrows():
 row={k:r[k] for k in K};row.update({'months_observed':0,'duplicate_month':False,'safety_period_complete':False})
 if pd.notna(r.fy_end_date) and r.fy_is_month_end and not r.fy_end_month_changed:
  end=r.fy_end_date.to_period('M');start=end-11
  row['safety_start_month']=str(start);row['safety_end_month']=str(end)
  z=lookup.get((r.ntd_id,r['mode'],r.type_of_service))
  if z is not None:
   z=z[z.period.between(start,end)];row['months_observed']=z.period.nunique();row['duplicate_month']=bool(z.duplicate_key.any())
   complete=len(z)==12 and z.period.nunique()==12 and not row['duplicate_month'];row['safety_period_complete']=complete
   for field in S:
    row[field+'_months']=int(z[field].notna().sum())
    row[field+'_fy']=z[field].sum(min_count=12) if complete else np.nan
 annual.append(row)
p=p.merge(pd.DataFrame(annual),on=K,validate='one_to_one')
p['injury_numeric_valid']=p[['operator_injuries_fy','total_employee_injuries_fy','vehicle_revenue_hours_fy']].notna().all(axis=1)&p.operator_injuries_fy.ge(0)&p.total_employee_injuries_fy.ge(0)&p.vehicle_revenue_hours_fy.gt(0)
p['operator_injuries_per100k_service_hours']=100000*p.operator_injuries_fy/p.vehicle_revenue_hours_fy
p['employee_injuries_per100k_service_hours']=100000*p.total_employee_injuries_fy/p.vehicle_revenue_hours_fy
p['service_intensity_measure_not_individual_injury_probability']=True
p['fta_safety_mode_scope']=~p['mode'].isin(['CR','AR','YR'])
p['coverage_eligible']=p.fta_safety_mode_scope&p.type_of_service.eq('DO')&p.expense_join.eq('both')&p.labor_numeric_valid&p.labor_quality_clear&p.safety_period_complete&p.injury_numeric_valid
p['review_screen_eligible']=p.coverage_eligible&~p.wage_ratio_review_flag
p['conventional_bus']=p['mode'].eq('MB')
p['assault_year_complete']=p.safety_period_complete&p.total_assaults_on_transit_workers_fy.notna()
p['ready_for_causal_inference']=False
save(p,'candidate_national_panel.csv')
save(p[p.conventional_bus],'bus_feasibility_panel.csv')
save(p[p.conventional_bus&p.review_screen_eligible],'bus_candidate_analysis_sample.csv')
rows=[]
for year,g in p.groupby('report_year'):
 b=g[g.conventional_bus]
 rows.append({'year':year,'employee_mode_rows':len(g),'agencies_employee_data':g.ntd_id.nunique(),'expense_matched_rows':int(g.expense_join.eq('both').sum()),'all_modes_coverage_eligible':int(g.coverage_eligible.sum()),'all_modes_review_screen_eligible':int(g.review_screen_eligible.sum()),'bus_employee_rows':len(b),'bus_expense_matched':int(b.expense_join.eq('both').sum()),'bus_labor_numeric_valid':int(b.labor_numeric_valid.sum()),'bus_quality_clear':int(b.labor_quality_clear.sum()),'bus_twelve_month_safety':int(b.safety_period_complete.sum()),'bus_coverage_eligible':int(b.coverage_eligible.sum()),'bus_review_screen_eligible':int(b.review_screen_eligible.sum()),'bus_assault_year_complete':int((b.review_screen_eligible & b.assault_year_complete).sum()),'bus_injury_positive':int((b.review_screen_eligible&b.operator_injuries_fy.gt(0)).sum()),'bus_noncalendar_fy':int(b.fy_end_date.dt.month.ne(12).sum())})
coverage=pd.DataFrame(rows);save(coverage,'coverage_by_year.csv')
ret=p[p.conventional_bus&p.review_screen_eligible];counts=ret.groupby('ntd_id').report_year.nunique();balanced=set(counts[counts.eq(6)].index)
save(ret[ret.ntd_id.isin(balanced)],'bus_balanced_six_year_sample.csv')
agency=ret.groupby('ntd_id').agg(agency=('agency','last'),state=('state','last'),years=('report_year','nunique'),first_year=('report_year','min'),last_year=('report_year','max'),positive_operator_injury_years=('operator_injuries_fy',lambda s:s.gt(0).sum()),operator_injury_total=('operator_injuries_fy','sum'),min_wage_expense_per_hour=('wage_expense_per_operating_hour','min'),max_wage_expense_per_hour=('wage_expense_per_operating_hour','max')).reset_index()
save(agency,'bus_agency_coverage.csv')
targets={'00001':'King County Metro','00040':'Sound Transit','50066':'Chicago CTA','30019':'SEPTA','30022':'Pittsburgh Regional Transit','90003':'BART','20008':'NYCT'}
t=p[p.ntd_id.isin(targets)].copy();t['requested_system']=t.ntd_id.map(targets);save(t,'requested_systems_audit.csv')
recon=[]
for name,data,ycol,amount,control,ca in [('employee',er,'report_year','total_hours','employee_controls.csv','hours'),('expense',x_parts[-1],'report_year','operators_wages','expense_controls.csv','wages'),('monthly',m,'year','vehicle_revenue_hours','monthly_controls.csv','vrh')]:
 c=pd.read_csv(RAW/control);group=data.groupby(ycol).agg(n_download=(amount,'size'),amount_download=(amount,'sum')).reset_index();z=group.merge(c,on=ycol,validate='one_to_one');z['row_difference']=z.n_download-z.n;z['amount_difference']=z.amount_download-z[ca]
 assert z.row_difference.eq(0).all() and z.amount_difference.abs().lt(.01).all()
 z['source']=name;recon.append(z)
save(pd.concat(recon,ignore_index=True),'api_control_reconciliation.csv')
save(p[p.wage_ratio_review_flag], 'wage_ratio_review_queue.csv')
save(pd.DataFrame(load_audit),'legacy_load_audit.csv')
summary={'employee_mode_years':len(p),'expense_join_matches':int(p.expense_join.eq('both').sum()),'all_mode_review_eligible_rows':int(p.review_screen_eligible.sum()),'all_mode_review_eligible_agencies':p.loc[p.review_screen_eligible,'ntd_id'].nunique(),'bus_candidate_agency_years':len(ret),'bus_candidate_unique_agencies':ret.ntd_id.nunique(),'balanced_bus_agencies':len(balanced),'balanced_bus_agency_years':len(ret[ret.ntd_id.isin(balanced)]),'bus_with_any_operator_injury':int(agency.positive_operator_injury_years.gt(0).sum()),'bus_with_multiple_years':int(counts.ge(2).sum()),'bus_assault_complete_agency_years':int(ret.assault_year_complete.sum()),'bus_q_or_w_flagged_rows':int((p.conventional_bus&~p.labor_quality_clear).sum()),'monthly_conflicting_key_rows':int(m.duplicate_key.sum()),'cash_identity_max_error_2019_2021':float(p.legacy_salary_identity_error.abs().max()),'hours_identity_max_error':float(p.hours_identity_error.abs().max()),'review_wage_range':[7.25,150],'causal_identification_established':False,'union_or_pay_standardization_measured':False}
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(coverage.to_string(index=False))
