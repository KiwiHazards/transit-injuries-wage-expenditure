"""Build fiscal-year controls and exact consecutive lags from frozen audit inputs."""
from pathlib import Path
import pandas as pd, numpy as np, re, json, hashlib, datetime

ROOT=Path(__file__).resolve().parent; RAW=ROOT/'raw'; OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
BASE=ROOT.parent/'national_transit_audit'
K=['ntd_id','report_year','mode','type_of_service']
H=['vehicle_operations_hours','vehicle_maintenance_hours','facility_maintenance_hours','general_administration_hours']
FIPS=dict(x.split(':') for x in 'AL:01 AK:02 AZ:04 AR:05 CA:06 CO:08 CT:09 DE:10 DC:11 FL:12 GA:13 HI:15 ID:16 IL:17 IN:18 IA:19 KS:20 KY:21 LA:22 ME:23 MD:24 MA:25 MI:26 MN:27 MS:28 MO:29 MT:30 NE:31 NV:32 NH:33 NJ:34 NM:35 NY:36 NC:37 ND:38 OH:39 OK:40 OR:41 PA:42 RI:44 SC:45 SD:46 TN:47 TX:48 UT:49 VT:50 VA:51 WA:53 WV:54 WI:55 WY:56 PR:72 VI:78'.split())
def save(d,n):d.to_csv(OUT/n,index=False,float_format='%.10g')
def norm(s):return re.sub(r'[^a-z0-9]+','_',str(s).lower()).strip('_')
def nid(x):
    s=str(x).strip()
    return str(int(float(s))).zfill(5) if re.fullmatch(r'\d+(?:\.0)?',s) else None

def main():
    p=pd.read_csv(BASE/'outputs/bus_candidate_analysis_sample.csv',dtype={'ntd_id':str})
    assert len(p)==1670 and not p.duplicated(K).any()
    p['fy_end_date']=pd.to_datetime(p.fy_end_date)
    c=pd.read_csv(RAW/'CPIAUCNS.csv'); c['month']=pd.to_datetime(c.iloc[:,0]).dt.to_period('M')
    c=c[c.month.between(pd.Period('2018-01'),pd.Period('2024-12'))]
    assert len(c)==84 and not c.month.duplicated().any() and c.CPIAUCNS.gt(0).all()
    reference=c[c.month.dt.year.eq(2024)].CPIAUCNS.mean(); cp=c.set_index('month').CPIAUCNS
    save(c.assign(month=c.month.astype(str)),'cpi_monthly_used.csv')
    qp=[]
    for f in sorted(RAW.glob('qcew_*_industry10.csv')):
        d=pd.read_csv(f,dtype={'area_fips':str,'industry_code':str},low_memory=False)
        d=d[d.area_fips.isin([v+'000' for v in FIPS.values()])&d.own_code.eq(5)&d.industry_code.eq('10')&d['size_code'].eq(0)].copy()
        assert d.agglvl_code.eq(51).all()
        qp.append(d)
    q=pd.concat(qp,ignore_index=True)
    assert len(qp)==28 and not q.duplicated(['area_fips','year','qtr']).any()
    q['mean_monthly_employment']=q[['month1_emplvl','month2_emplvl','month3_emplvl']].mean(axis=1)
    q['weekly_wage_unrounded']=q.total_qtrly_wages/(13*q.mean_monthly_employment)
    q['weekly_wage_rounding_error']=q.weekly_wage_unrounded-q.avg_wkly_wage
    valid=q.disclosure_code.fillna('').str.strip().eq('')&q.mean_monthly_employment.gt(0)
    assert q.loc[valid,'weekly_wage_rounding_error'].abs().max()<=.501
    q.loc[~valid,'weekly_wage_unrounded']=np.nan
    save(q,'state_private_qcew_quarterly.csv')
    monthly=[]
    for _,r in q.iterrows():
        for j in range(1,4):
            monthly.append({'area_fips':r.area_fips,'month':pd.Period(year=int(r.year),month=(int(r.qtr)-1)*3+j,freq='M'),'market_weekly_wage':r.weekly_wage_unrounded,'market_employment':r[f'month{j}_emplvl']})
    qm=pd.DataFrame(monthly).set_index(['area_fips','month'])
    fiscal=[]
    for _,r in p.iterrows():
        months=pd.period_range(r.safety_start_month,r.safety_end_month,freq='M')
        assert len(months)==12
        inflation=cp.reindex(months)
        area=FIPS[r.state]+'000'
        z=qm.reindex(pd.MultiIndex.from_product([[area],months],names=['area_fips','month']))
        complete=z[['market_weekly_wage','market_employment']].notna().all(axis=1).sum()
        mw=np.average(z.market_weekly_wage,weights=z.market_employment) if complete==12 else np.nan
        fiscal.append({'ntd_id':r.ntd_id,'report_year':r.report_year,'cpi_fy':inflation.mean() if inflation.notna().sum()==12 else np.nan,'cpi_months':inflation.notna().sum(),'market_months':int(complete),'state_market_weekly_wage':mw,'market_partial_quarter_approximation':r.fy_end_date.month not in [3,6,9,12]})
    p=p.merge(pd.DataFrame(fiscal),on=['ntd_id','report_year'],validate='one_to_one')
    p['real_wage_per_hour']=p.wage_expense_per_operating_hour*reference/p.cpi_fy
    p['real_compensation_per_hour']=p.compensation_expense_per_operating_hour*reference/p.cpi_fy
    p.loc[p.benefit_flagged|p.real_compensation_per_hour.le(0),'real_compensation_per_hour']=np.nan
    p['real_market_weekly_wage']=p.state_market_weekly_wage*reference/p.cpi_fy
    for src,dst in [('real_wage_per_hour','log_real_wage'),('real_compensation_per_hour','log_real_compensation'),('real_market_weekly_wage','log_real_market_wage'),('vehicle_revenue_hours_fy','log_service_hours'),('wage_expense_per_operating_hour','log_nominal_wage')]:p[dst]=np.log(p[src].where(p[src].gt(0)))
    p['injury_rate']=p.operator_injuries_per100k_service_hours
    p['log1p_injury_rate']=np.log1p(p.injury_rate)
    p['employee_injury_labor_rate']=1e5*p.total_employee_injuries_fy/p.operating_hours
    p['operator_injury_mileage_rate']=1e6*p.operator_injuries_fy/p.vehicle_revenue_miles_fy.where(p.vehicle_revenue_miles_fy.gt(0))
    for h in H:p[h.replace('_hours','_share')]=p[h]/p.operating_hours
    # Recover part-time operating hours independently from FT/PT source sheets.
    parts=[]
    for year in [2019,2020,2021]:
        for typ,sheet in [('ft','Full Time Employees by Mode'),('pt','Part Time Employees by Mode')]:
            d=pd.read_excel(BASE/'raw'/f'employees_{year}.xlsx',sheet_name=sheet)
            d.columns=[norm(v) for v in d.columns]; d=d.rename(columns={'tos':'type_of_service'})
            d['ntd_id']=d.ntd_id.map(nid);d=d[d.ntd_id.notna()];d['report_year']=year
            d['hours']=d[H].sum(axis=1,min_count=4);d['typ']=typ
            parts.append(d[K+['hours','typ']])
    d=pd.read_csv(BASE/'raw/employees_2022_2024.csv',dtype={'ntd_id':str});d.ntd_id=d.ntd_id.map(nid);d=d[d.report_year.isin([2022,2023])].copy()
    d['typ']=d.full_or_part_time.map({'Full Time':'ft','Part Time':'pt'});d['hours']=d[H].sum(axis=1,min_count=4);parts.append(d[K+['hours','typ']])
    d=pd.read_excel(BASE/'raw/employees_raw_2024.xlsx').rename(columns={'NTD ID':'ntd_id','Mode':'mode','TOS':'type_of_service'});d.ntd_id=d.ntd_id.map(nid);d['report_year']=2024
    for typ,name in [('ft','Full Time'),('pt','Part Time')]:
        z=d[K].copy();z['typ']=typ;z['hours']=d[f'Total {name} (Operating Labor) Hours Worked'];parts.append(z)
    mix=pd.concat(parts,ignore_index=True).pivot(index=K,columns='typ',values='hours').reset_index().rename(columns={'ft':'fulltime_operating_hours','pt':'parttime_operating_hours'})
    p=p.merge(mix,on=K,validate='one_to_one')
    p['ftpt_reconciliation_error']=p.fulltime_operating_hours+p.parttime_operating_hours-p.operating_hours
    assert p.ftpt_reconciliation_error.notna().all() and p.ftpt_reconciliation_error.abs().max()<.01
    p['parttime_hour_share']=p.parttime_operating_hours/p.operating_hours
    assert p.parttime_hour_share.between(0,1).all()
    lagvars=['injury_rate','log1p_injury_rate','employee_injury_labor_rate','operator_injury_mileage_rate','log_real_wage','log_service_hours','log_real_market_wage','vehicle_maintenance_share','facility_maintenance_share','general_administration_share','parttime_hour_share','fy_end_date','real_wage_per_hour','wage_expense_per_operating_hour','market_partial_quarter_approximation']
    lag=p[['ntd_id','report_year']+lagvars].copy();lag['report_year']+=1;lag=lag.rename(columns={v:'lag_'+v for v in lagvars})
    p=p.merge(lag,on=['ntd_id','report_year'],how='left',validate='one_to_one')
    p['exact_lag_pair']=p.lag_fy_end_date.notna()&((p.fy_end_date.dt.year-p.lag_fy_end_date.dt.year)*12+p.fy_end_date.dt.month-p.lag_fy_end_date.dt.month).eq(12)
    p.loc[~p.exact_lag_pair,['lag_'+v for v in lagvars if v!='fy_end_date']]=np.nan
    p['wage_change_fraction']=p.real_wage_per_hour/p.lag_real_wage_per_hour-1
    p['large_wage_change']=p.wage_change_fraction.abs().gt(.5)
    p['state_year']=p.state+'_'+p.report_year.astype(str)
    count=p.groupby('ntd_id').report_year.nunique();p['balanced_six_years']=p.ntd_id.isin(count[count.eq(6)].index)
    p['in_50_states_dc']=~p.state.isin(['PR','VI'])
    save(p,'augmented_bus_panel.csv')
    save(p[p.large_wage_change][['ntd_id','agency','report_year','real_wage_per_hour','lag_real_wage_per_hour','wage_change_fraction','operating_hours','operating_wages']],'large_wage_change_review.csv')
    save(p[['ntd_id','report_year','state','fy_end_date','cpi_fy','cpi_months','market_months','state_market_weekly_wage','market_partial_quarter_approximation','ftpt_reconciliation_error','exact_lag_pair']],'control_join_audit.csv')
    summary={'base_rows':len(p),'agencies':p.ntd_id.nunique(),'cpi_complete_rows':int(p.cpi_months.eq(12).sum()),'qcew_complete_rows':int(p.market_months.eq(12).sum()),'exact_lag_pairs':int(p.exact_lag_pair.sum()),'parttime_share_complete':int(p.parttime_hour_share.notna().sum()),'partial_quarter_rows':int(p.market_partial_quarter_approximation.sum()),'cpi_2024_reference':reference,'ftpt_identity_max_error':float(p.ftpt_reconciliation_error.abs().max()),'qcew_rounding_max_error':float(q.loc[valid,'weekly_wage_rounding_error'].abs().max()),'large_wage_change_rows':int(p.large_wage_change.sum()),'analysis_plan_sha256':hashlib.sha256((ROOT/'ANALYSIS_PLAN.md').read_bytes()).hexdigest(),'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (OUT/'preparation_summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
