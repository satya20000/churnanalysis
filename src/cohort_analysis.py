"""Month-end cohort retention and Kaplan–Meier with Greenwood confidence intervals."""
import numpy as np
import pandas as pd
from data_processing import AS_OF, OUT

def cohorts(c):
    c=c.copy();c['cohort']=c.started_at.dt.to_period('M').dt.to_timestamp()
    rows=[]
    for cohort,g in c.groupby('cohort'):
        for age in range(36):
            end=cohort+pd.DateOffset(months=age)+pd.offsets.MonthEnd(0)
            observable=end<=AS_OF
            retained=int((g.ended_at.isna()|(g.ended_at>end)).sum()) if observable else None
            rows.append({'cohort':cohort,'age_months':age,'cohort_size':len(g),'retained':retained,'retention':retained/len(g) if observable else None,'observable':int(observable)})
    result=pd.DataFrame(rows);result.to_csv(OUT/'cohort_retention.csv',index=False)
    # Account-grain version preserves plan/segment/channel filters and recomputes cohort weights.
    detail=[]
    for _,s in c.iterrows():
        for age in range(36):
            end=s.cohort+pd.DateOffset(months=age)+pd.offsets.MonthEnd(0)
            if end>AS_OF:break
            detail.append({'account_id':s.account_id,'plan_id':s.plan_id,'cohort':s.cohort,'age_months':age,'retained':int(pd.isna(s.ended_at) or s.ended_at>end),'cohort_accounts':1})
    pd.DataFrame(detail).to_csv(OUT/'fact_cohort.csv',index=False)
    return result

def kaplan_meier(duration,event):
    duration=np.asarray(duration);event=np.asarray(event,dtype=bool)
    survival=1.;greenwood=0.;rows=[{'day':0,'survival':1.,'lower95':1.,'upper95':1.,'at_risk':len(duration),'events':0}]
    for t in np.unique(duration):
        n=int((duration>=t).sum());d=int(((duration==t)&event).sum())
        if not d:continue
        survival*=1-d/n
        if n>d:greenwood+=d/(n*(n-d))
        if 0<survival<1:
            se=np.sqrt(greenwood)/abs(np.log(survival));z=np.log(-np.log(survival))
            low=np.exp(-np.exp(z+1.96*se));high=np.exp(-np.exp(z-1.96*se))
        else:low=high=survival
        rows.append({'day':int(t),'survival':survival,'lower95':low,'upper95':high,'at_risk':n,'events':d})
    return pd.DataFrame(rows)

def survival(c):
    rows=[]
    for dim in ['plan_name','segment','acquisition_channel']:
        for group,g in c.groupby(dim):
            k=kaplan_meier(g.tenure_days,g.ended_at.notna());k['dimension']=dim;k['group']=group;rows.append(k)
    result=pd.concat(rows,ignore_index=True);result.to_csv(OUT/'survival_curves.csv',index=False)
    return result
