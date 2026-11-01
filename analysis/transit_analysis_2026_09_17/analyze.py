"""Prespecified associational models; transparent QR OLS and agency-clustered CR1.

No model-selection by significance. Uses numpy/scipy already available in runtime.
The primary fit is independently checked against an explicit dummy-variable SVD fit.
"""
from pathlib import Path
import json, datetime, hashlib
import numpy as np, pandas as pd
from scipy import linalg, stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'outputs';FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
CONTROL=['lag_log_service_hours','lag_vehicle_maintenance_share','lag_facility_maintenance_share','lag_general_administration_share','lag_parttime_hour_share','log_real_market_wage']
def save(d,n):d.to_csv(OUT/n,index=False,float_format='%.10g')

def fit(data,y,x,controls=(),effects=('ntd_id','report_year'),check=False):
    needed=list(dict.fromkeys([y,x,'ntd_id',*controls,*effects]))
    z=data.replace([np.inf,-np.inf],np.nan).dropna(subset=needed).copy()
    before=len(z)
    if 'ntd_id' in effects:
        counts=z.groupby('ntd_id').ntd_id.transform('size');z=z[counts.ge(2)].copy()
    z=z.reset_index(drop=True);n=len(z);g=z.ntd_id.nunique(); names=[x,*controls]
    X=z[names].to_numpy(float);Y=z[y].to_numpy(float)
    blocks=[np.ones((n,1))]+[pd.get_dummies(z[c].astype(str),drop_first=True,dtype=float).to_numpy() for c in effects]
    D=np.column_stack(blocks)
    Q,R,piv=linalg.qr(D,mode='economic',pivoting=True)
    diag=np.abs(np.diag(R));tol=max(D.shape)*np.finfo(float).eps*(diag.max() if len(diag) else 1)
    rd=int((diag>tol).sum());Q=Q[:,:rd]
    XR=X-Q@(Q.T@X);YR=Y-Q@(Q.T@Y)
    b,_,rank,svals=linalg.lstsq(XR,YR,lapack_driver='gelsd')
    if rank!=len(names):raise ValueError('Unidentified substantive regressors: '+str(names))
    residual=YR-XR@b
    bread=linalg.inv(XR.T@XR)
    codes,_=pd.factorize(z.ntd_id,sort=True);scores=np.zeros((g,len(names)))
    np.add.at(scores,codes,XR*residual[:,None])
    correction=g/(g-1)*(n-1)/(n-rd-len(names))
    covariance=bread@(scores.T@scores)@bread*correction
    se=np.sqrt(np.diag(covariance));tval=b/se;pv=2*stats.t.sf(np.abs(tval),g-1);crit=stats.t.ppf(.975,g-1)
    co=pd.DataFrame({'term':names,'estimate':b,'cluster_se':se,'p_two_sided':pv,'ci_low':b-crit*se,'ci_high':b+crit*se})
    meta={'n':n,'agencies':g,'years':','.join(map(str,sorted(z.report_year.unique()))),'singleton_rows_removed':before-n,'nuisance_rank':rd,'design_rank':rd+len(names),'residual_df':n-rd-len(names),'inference_df':g-1,'cr1_correction':correction,'partial_r2':1-float(residual@residual)/float(YR@YR),'predictor_residual_sd':float(XR[:,0].std(ddof=1))}
    if check:
        DD=D[:,piv[:rd]];full=np.column_stack([X,DD]);bf,_,rf,_=linalg.lstsq(full,Y,lapack_driver='gelsd')
        assert rf==full.shape[1]
        uf=Y-full@bf;inv=linalg.pinv(full)
        sums=np.stack([inv[:,codes==j]@uf[codes==j] for j in range(g)])
        cv=sums.T@sums*correction
        checks={'primary_beta_max_difference':float(np.max(np.abs(bf[:len(names)]-b))),'primary_cluster_cov_max_difference':float(np.max(np.abs(cv[:len(names),:len(names)]-covariance))),'normal_equations_max':float(np.max(np.abs(XR.T@residual)))}
        assert checks['primary_beta_max_difference']<1e-8 and checks['primary_cluster_cov_max_difference']<1e-8
        (OUT/'independent_regression_checks.json').write_text(json.dumps(checks,indent=2))
    return co,meta,z,XR,YR,residual

def main():
    p=pd.read_csv(OUT/'augmented_bus_panel.csv',dtype={'ntd_id':str})
    p['fy_end_date']=pd.to_datetime(p.fy_end_date)
    lag=p[p.exact_lag_pair].copy()
    complete=lag.dropna(subset=['log_real_wage','lag_injury_rate',*CONTROL])
    top=p.groupby('ntd_id').vehicle_revenue_hours_fy.mean().nlargest(5).index
    save(p[p.ntd_id.isin(top)][['ntd_id','agency','report_year','vehicle_revenue_hours_fy']],'largest_five_agencies.csv')
    # Exact lists fixed in ANALYSIS_PLAN.md before regression output was inspected.
    specs=[
      ('D0','Descriptive pooled, same year',p,'log_real_wage','injury_rate',[],('report_year',)),
      ('D1','Same-year agency and year effects',p,'log_real_wage','injury_rate',[],('ntd_id','report_year')),
      ('L0','Lagged, agency and year effects',complete,'log_real_wage','lag_injury_rate',[],('ntd_id','report_year')),
      ('P1','Primary: lagged, adjusted',complete,'log_real_wage','lag_injury_rate',CONTROL,('ntd_id','report_year')),
      ('S1','Balanced six-year cohort',complete[complete.balanced_six_years],'log_real_wage','lag_injury_rate',CONTROL,('ntd_id','report_year')),
      ('S2','Neither year is 2020 or 2021',complete[~complete.report_year.isin([2020,2021,2022])],'log_real_wage','lag_injury_rate',CONTROL,('ntd_id','report_year')),
      ('S3','Both fiscal windows end before 2023',complete[complete.fy_end_date.lt('2023-01-01')],'log_real_wage','lag_injury_rate',CONTROL,('ntd_id','report_year')),
      ('S4','Exclude five largest agencies',complete[~complete.ntd_id.isin(top)],'log_real_wage','lag_injury_rate',CONTROL,('ntd_id','report_year')),
      ('S5','Log(1 + prior injury rate)',complete,'log_real_wage','lag_log1p_injury_rate',CONTROL,('ntd_id','report_year')),
      ('S6','Employee injuries per labor hour',complete,'log_real_wage','lag_employee_injury_labor_rate',CONTROL,('ntd_id','report_year')),
      ('S7','Compensation including benefits',complete,'log_real_compensation','lag_injury_rate',CONTROL,('ntd_id','report_year')),
      ('S8','Agency and state-by-year effects',complete,'log_real_wage','lag_injury_rate',CONTROL[:-1],('ntd_id','state_year')),
      ('S9','Nominal wage outcome',complete,'log_nominal_wage','lag_injury_rate',CONTROL,('ntd_id','report_year')),
      ('S10','Exclude wage changes over 50%',complete[~complete.large_wage_change],'log_real_wage','lag_injury_rate',CONTROL,('ntd_id','report_year')),
      ('E1','Exploratory: prior wages, later injury',lag,'log1p_injury_rate','lag_log_real_wage',CONTROL,('ntd_id','report_year')),
    ]
    rows=[];coef=[];membership=[];primary=None
    for id,label,d,y,x,controls,fe in specs:
        c,m,z,xr,yr,u=fit(d,y,x,controls,fe,check=id=='P1')
        first=c.iloc[0].to_dict();rows.append({'model':id,'label':label,'outcome':y,'predictor':x,**m,**first})
        c['model']=id;coef.append(c);membership.append(z[['ntd_id','report_year']].assign(model=id))
        if id=='P1':primary=(z,xr,yr,u)
        print(id,'n',m['n'],'agencies',m['agencies'],'b',round(first['estimate'],6),'p',round(first['p_two_sided'],4),flush=True)
    models=pd.DataFrame(rows);save(models,'model_results.csv');save(pd.concat(coef,ignore_index=True),'all_substantive_coefficients.csv');save(pd.concat(membership,ignore_index=True),'model_membership.csv')
    # Additional diagnostics explicitly labeled, not alternate preferred models.
    save(p[['real_wage_per_hour','wage_expense_per_operating_hour','injury_rate','operator_injuries_fy','vehicle_revenue_hours_fy','operating_hours','parttime_hour_share','real_market_weekly_wage']].describe(percentiles=[.01,.25,.5,.75,.95,.99]).reset_index().rename(columns={'index':'statistic'}),'descriptive_statistics.csv')
    yr=[]
    for scope,d in [('all_screened',p),('balanced',p[p.balanced_six_years])]:
        for y,z in d.groupby('report_year'):
            yr.append({'scope':scope,'year':y,'agencies':len(z),'nominal_wage_median':z.wage_expense_per_operating_hour.median(),'real_wage_median':z.real_wage_per_hour.median(),'injury_rate_median':z.injury_rate.median(),'injury_rate_mean':z.injury_rate.mean(),'injury_rate_pooled_exposure':1e5*z.operator_injuries_fy.sum()/z.vehicle_revenue_hours_fy.sum(),'operator_injuries':z.operator_injuries_fy.sum(),'zero_injury_share':z.operator_injuries_fy.eq(0).mean(),'service_hours':z.vehicle_revenue_hours_fy.sum()})
    annual=pd.DataFrame(yr);save(annual,'annual_descriptives.csv')
    variation=p.groupby('ntd_id').agg(years=('report_year','nunique'),injury_sd=('injury_rate','std'),wage_sd=('log_real_wage','std'),injury_total=('operator_injuries_fy','sum')).reset_index();save(variation,'within_agency_variation.csv')
    z,xr,yr,u=primary
    # Partial-out other covariates as well as fixed effects for a diagnostic scatter.
    other=xr[:,1:];xp=xr[:,0]-other@linalg.lstsq(other,xr[:,0])[0];yp=yr-other@linalg.lstsq(other,yr)[0]
    save(z[['ntd_id','report_year']].assign(residualized_lag_injury=xp,residualized_log_wage=yp,residual=u),'primary_partial_regression.csv')
    score=z[['ntd_id','agency']].copy();score['score']=xp*u
    influence=score.groupby(['ntd_id','agency']).score.sum().reset_index();influence['absolute_score']=influence.score.abs();save(influence.sort_values('absolute_score',ascending=False),'primary_cluster_score_diagnostic.csv')
    result={'models_estimated':len(models),'base_agencies':p.ntd_id.nunique(),'base_rows':len(p),'lag_pairs':len(lag),'primary_n':len(z),'primary_agencies':z.ntd_id.nunique(),'all_zero_injury_agencies':int(variation.injury_total.eq(0).sum()),'agencies_with_injury_variation':int(variation.injury_sd.gt(1e-10).sum()),'base_zero_injury_fraction':float(p.operator_injuries_fy.eq(0).mean()),'plan_sha256':hashlib.sha256((ROOT/'ANALYSIS_PLAN.md').read_bytes()).hexdigest(),'run_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'causal_identification':False,'literature_review_complete':False}
    (OUT/'analysis_summary.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
    plot(annual,models,p,xp,yp)

def plot(annual,models,p,xp,yp):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150,'savefig.dpi':220})
    blue='#17617D';orange='#C36632'
    a=annual[annual.scope.eq('balanced')]
    fig,axs=plt.subplots(1,2,figsize=(11,4.6))
    axs[0].plot(a.year,a.nominal_wage_median,'o-',color=orange,label='Nominal dollars')
    axs[0].plot(a.year,a.real_wage_median,'o-',color=blue,label='2024 dollars')
    axs[0].set_ylabel('Median wage expenditure / operating labor hour ($)');axs[0].set_title('Compensation over time');axs[0].legend(frameon=False)
    axs[1].plot(a.year,a.injury_rate_pooled_exposure,'o-',color=blue)
    axs[1].set_ylabel('Reported operator injuries / 100,000 service hours');axs[1].set_title('Injury intensity, pooled by exposure');axs[1].set_ylim(bottom=0)
    for ax in axs:ax.set_xticks(a.year);ax.grid(axis='y',alpha=.18);ax.set_xlabel('NTD report year')
    fig.suptitle('245 bus agencies observed in all six years',fontsize=14,fontweight='bold')
    fig.text(.05,.015,'Source: matched NTD records; fiscal-year CPI-U adjustment. Descriptive trends do not establish a causal relationship.',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.94]);fig.savefig(FIG/'balanced_trends.png');fig.savefig(FIG/'balanced_trends.pdf');plt.close(fig)
    m=models[models.model.isin(['P1','S1','S2','S3','S4','S8','S9','S10'])].copy();yy=np.arange(len(m))
    fig,ax=plt.subplots(figsize=(9.5,5.6));b=100*np.expm1(m.estimate);lo=100*np.expm1(m.ci_low);hi=100*np.expm1(m.ci_high)
    ax.errorbar(b,yy,xerr=np.vstack([b-lo,hi-b]),fmt='o',color=blue,ecolor=blue,capsize=3)
    ax.axvline(0,color='#555555',lw=1,ls='--');ax.set_yticks(yy,m.label);ax.invert_yaxis();ax.set_xlabel('Wage expenditure difference (%) per +1 prior injury / 100,000 service hours')
    ax.set_title('Primary estimate and prespecified sensitivity checks',loc='left',fontweight='bold');ax.grid(axis='x',alpha=.18)
    fig.text(.02,.015,'Points: associational estimates. Bars: 95% agency-clustered confidence intervals. Samples differ across checks.',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,1]);fig.savefig(FIG/'coefficient_sensitivity.png');fig.savefig(FIG/'coefficient_sensitivity.pdf');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10.5,4.5))
    axs[0].hist(p.real_wage_per_hour,bins=35,color=blue,edgecolor='white');axs[0].set_xlabel('Wage expenditure / labor hour (2024 $)');axs[0].set_ylabel('Agency-year observations');axs[0].set_title('Wage expenditure distribution')
    axs[1].hist(p.injury_rate,bins=35,color=orange,edgecolor='white');axs[1].set_xlabel('Operator injuries / 100,000 service hours');axs[1].set_ylabel('Agency-year observations');axs[1].set_title('Injury intensity, including zeros')
    fig.tight_layout();fig.savefig(FIG/'distributions.png');fig.savefig(FIG/'distributions.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4.8));ax.scatter(xp,yp,s=10,alpha=.22,color=blue);b=models.loc[models.model.eq('P1'),'estimate'].iloc[0];xx=np.array([xp.min(),xp.max()]);ax.plot(xx,b*xx,color=orange)
    ax.set_xlabel('Prior injury intensity, residualized');ax.set_ylabel('Log real wage expenditure, residualized');ax.set_title('Primary model: association after controls',loc='left',fontweight='bold')
    fig.text(.03,.015,'Each point is an agency-year. Fixed effects and controls removed; the fitted line is not a causal effect.',fontsize=8.5)
    fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(FIG/'partial_association.png');fig.savefig(FIG/'partial_association.pdf');plt.close(fig)

if __name__=='__main__':main()
