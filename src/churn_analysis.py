"""Fixed landmark design: past 30-day signals, future 90-day churn. No post-event fields."""
import pandas as pd
from data_processing import OUT, billing_features
from cohort_analysis import kaplan_meier

def landmark(data,c,cutoff):
    cutoff=pd.Timestamp(cutoff)
    eligible=c[(c.started_at<=cutoff-pd.Timedelta(days=30))&(c.ended_at.isna()|(c.ended_at>cutoff))].copy()
    f=billing_features(data,cutoff)
    eligible=eligible.merge(f.drop(columns=['account_id','mrr']),on='subscription_id',validate='one_to_one')
    eligible['landmark']=cutoff
    eligible['tenure_at_landmark']=(cutoff-eligible.started_at).dt.days
    eligible['churn_next90']=eligible.ended_at.between(cutoff+pd.Timedelta(days=1),cutoff+pd.Timedelta(days=90)).astype(int)
    return eligible

def signals(data,c):
    allrows=[]
    for date in ['2024-06-30','2024-09-30','2024-12-31','2025-03-31','2025-06-30','2025-09-30']:
        f=landmark(data,c,date);allrows.append(f)
    f=pd.concat(allrows,ignore_index=True);f.to_csv(OUT/'landmark_features.csv',index=False)
    comparison=f.groupby(['landmark','risk_group']).agg(accounts=('account_id','size'),churned=('churn_next90','sum'))
    comparison['churn_90d']=comparison.churned/comparison.accounts
    comparison.to_csv(OUT/'landmark_billing_churn.csv')
    latest=f[f.landmark==pd.Timestamp('2025-09-30')].copy()
    latest['residual_days']=(latest.ended_at.fillna(pd.Timestamp('2025-12-31'))-latest.landmark).dt.days
    rows=[]
    for group,g in latest.groupby('risk_group'):
        k=kaplan_meier(g.residual_days,g.ended_at.notna());k['group']=group;rows.append(k)
    pd.concat(rows,ignore_index=True).to_csv(OUT/'landmark_survival.csv',index=False)
    # Deliberately omit optional classifier: association design is primary and has honest sample sizes.
    return f,comparison.reset_index()
