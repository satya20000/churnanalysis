"""Version-pinned source ingestion and event-time SaaS marts. Run from repository root."""
from pathlib import Path
import hashlib, json, sqlite3, urllib.request, zipfile
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT/'data/raw', ROOT/'data/processed'
AS_OF = pd.Timestamp('2025-12-31')
URL = 'https://uhzz8xwe8uih5iol.public.blob.vercel-storage.com/datasets/saas-subscriptions/v1.0.0/saas-subscriptions-v1.0.0-source-csv.zip'
TABLES = ['accounts', 'plans', 'subscriptions', 'invoices', 'payments']

def load():
    if not all((RAW/f'{t}.csv').exists() for t in TABLES):
        RAW.mkdir(parents=True, exist_ok=True)
        archive=ROOT/'data/source.zip'
        urllib.request.urlretrieve(URL, archive)
        with zipfile.ZipFile(archive) as z:
            for name in TABLES + ['LICENSE.txt', 'DATA_DICTIONARY.md', 'README.md']:
                z.extract(name + '.csv' if name in TABLES else name, RAW)
    data={t:pd.read_csv(RAW/f'{t}.csv', keep_default_na=False).replace('', np.nan) for t in TABLES}
    for d in data.values():
        for c in d.columns:
            if c.endswith('_at') or c.endswith('_date'):
                d[c]=pd.to_datetime(d[c])
    return data

def quality(data):
    checks=[]
    def check(name, passed, detail):
        checks.append({'check':name,'passed':bool(passed),'detail':str(detail)})
    keys=dict(zip(TABLES,['account_id','plan_id','subscription_id','invoice_id','payment_id']))
    for t,d in data.items():
        check(t+' primary key',d[keys[t]].is_unique and d[keys[t]].notna().all(),len(d))
        check(t+' duplicate rows',not d.duplicated().any(),int(d.duplicated().sum()))
        check(t+' required fields',d.drop(columns=['ended_at'],errors='ignore').notna().all().all(),d.isna().sum().to_dict())
    for child,fk,parent in [('subscriptions','account_id','accounts'),('subscriptions','plan_id','plans'),('invoices','subscription_id','subscriptions'),('payments','invoice_id','invoices')]:
        check(child+' '+fk+' foreign key',data[child][fk].isin(data[parent][fk]).all(),'All parents exist')
    s,i,p=data['subscriptions'],data['invoices'],data['payments']
    check('one subscription per account',s.account_id.is_unique,len(s))
    check('end after start',(s.ended_at.isna() | (s.ended_at>s.started_at)).all(),'Cancellation effective on ended_at')
    check('status agrees with dates',((s.status=='active')==s.ended_at.isna()).all(),s.status.value_counts().to_dict())
    check('positive subscription values',((s.mrr>0)&(s.seats>0)).all(),'MRR and seats')
    check('positive billed and attempted values',(i.amount_due>=0).all() and (p.amount>=0).all(),'No negative amounts')
    check('due date on or after invoice',(i.due_date>=i.invoice_date).all(),'Date ordering')
    payment=p.merge(i[['invoice_id','invoice_date','amount_due']],on='invoice_id',validate='many_to_one')
    check('attempt not before invoice',(payment.attempted_at>=payment.invoice_date).all(),'Payment timeline')
    success=p[p.payment_status=='succeeded'].groupby('invoice_id').amount.sum()
    inv=i.set_index('invoice_id')
    check('successful collection not above due',(success<=inv.amount_due.reindex(success.index)+.005).all(),'Retry attempts are not revenue')
    check('paid invoices reconcile',np.allclose(inv[inv.invoice_status=='paid'].amount_due,success.reindex(inv[inv.invoice_status=='paid'].index).fillna(0)),'Exact successful payment value')
    check('source within coverage',all(d[c].dropna().le(AS_OF).all() for d in data.values() for c in d if c.endswith('_at') or c.endswith('_date')),'Last observed date 2025-12-31')
    pd.DataFrame(checks).to_csv(OUT/'quality_checks.csv',index=False)
    profiles={t:{'rows':len(d),'columns':len(d.columns),'dtypes':d.dtypes.astype(str).to_dict(),'missing':d.isna().sum().to_dict(),'numeric_summary':d.describe(include='number').to_dict() if len(d.select_dtypes('number').columns) else {},'date_ranges':{c:[str(d[c].min()),str(d[c].max())] for c in d if pd.api.types.is_datetime64_any_dtype(d[c])},'categories':{c:d[c].value_counts().to_dict() for c in d.select_dtypes('object') if d[c].nunique()<20}} for t,d in data.items()}
    (OUT/'source_profile.json').write_text(json.dumps(profiles,indent=2,default=str))
    (OUT/'source_manifest.json').write_text(json.dumps({'version':'1.0.0','as_of':str(AS_OF.date()),'source_url':URL,'classification':'synthetic educational data','sha256':{t:hashlib.sha256((RAW/f'{t}.csv').read_bytes()).hexdigest() for t in TABLES}},indent=2))
    if not all(c['passed'] for c in checks):
        raise ValueError([c for c in checks if not c['passed']])
    return checks

def customer_frame(data):
    return data['subscriptions'].merge(data['accounts'],on='account_id',validate='one_to_one').merge(data['plans'],on='plan_id',validate='many_to_one')

def billing_features(data, cutoff, window=30):
    """No final invoice_status in historical features: reconstruct unpaid balance from events."""
    s,i,p=data['subscriptions'],data['invoices'],data['payments']
    inv=i[i.invoice_date<=cutoff].copy()
    pay=p[p.attempted_at<=cutoff].merge(inv[['invoice_id','subscription_id']],on='invoice_id',validate='many_to_one')
    collected=pay[pay.payment_status=='succeeded'].groupby('invoice_id').amount.sum()
    inv['unpaid']=np.maximum(0,inv.amount_due-inv.invoice_id.map(collected).fillna(0))
    overdue=inv[(inv.due_date<=cutoff-pd.Timedelta(days=30))&(inv.unpaid>.005)].groupby('subscription_id').agg(overdue_invoices=('invoice_id','size'),overdue_value=('unpaid','sum'))
    recent=pay[pay.attempted_at>cutoff-pd.Timedelta(days=window)]
    failed=recent[recent.payment_status=='failed'].groupby('subscription_id').size()
    attempts=recent.groupby('subscription_id').size()
    retries=recent.groupby(['subscription_id','invoice_id']).size().gt(1).groupby('subscription_id').sum()
    lastfail=pay[pay.payment_status=='failed'].groupby('subscription_id').attempted_at.max()
    f=s[['subscription_id','account_id','mrr']].set_index('subscription_id').join(overdue)
    f['failed_30d']=failed;f['attempts_30d']=attempts;f['retried_invoices_30d']=retries
    f['days_since_failure']=(cutoff-lastfail.reindex(f.index)).dt.days
    f[['overdue_invoices','overdue_value','failed_30d','attempts_30d','retried_invoices_30d']]=f[['overdue_invoices','overdue_value','failed_30d','attempts_30d','retried_invoices_30d']].fillna(0)
    f['risk_flag']=((f.failed_30d>0)|(f.overdue_invoices>0)|(f.retried_invoices_30d>0)).astype(int)
    f['risk_group']=np.select([f.failed_30d>=2,f.failed_30d==1],['2+ failures','1 failure'],default='0 failures')
    return f.reset_index()

def build(data):
    OUT.mkdir(parents=True,exist_ok=True)
    quality(data)
    c=customer_frame(data)
    snapshots=[]
    for start in pd.date_range('2023-01-01',AS_OF,freq='MS'):
        end=start+pd.offsets.MonthEnd()
        f=c[['subscription_id','account_id','plan_id']].copy()
        f['month_start']=start;f['month_end']=end
        bop=(c.started_at<start)&(c.ended_at.isna()|(c.ended_at>=start))
        active=(c.started_at<=end)&(c.ended_at.isna()|(c.ended_at>end))
        new=c.started_at.between(start,end)
        churn=c.ended_at.between(start,end)
        f['beginning_customers']=bop.astype(int);f['active_customers']=active.astype(int)
        f['new_customers']=new.astype(int);f['churned_customers']=churn.astype(int)
        f['beginning_mrr']=c.mrr*bop;f['active_mrr']=c.mrr*active
        f['new_mrr']=c.mrr*new;f['churned_mrr']=c.mrr*churn
        f['bop_churned_customers']=(bop&churn).astype(int);f['bop_churned_mrr']=c.mrr*(bop&churn)
        f['churned_tenure_days']=(c.ended_at-c.started_at).dt.days.fillna(0)*churn
        risk=billing_features(data,end).set_index('subscription_id')
        f['mrr_at_risk']=c.mrr*active*f.subscription_id.map(risk.risk_flag)
        f['risk_accounts']=active.astype(int)*f.subscription_id.map(risk.risk_flag)
        # Keep inactive account-month rows for event counts and slicer-safe cohorts.
        snapshots.append(f)
    snap=pd.concat(snapshots,ignore_index=True)
    snap.to_csv(OUT/'subscription_monthly_snapshot.csv',index=False)
    snap.to_csv(OUT/'subscription_monthly_snapshot.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    numeric=snap.select_dtypes('number').columns
    monthly=snap.groupby('month_start')[numeric].sum().reset_index()
    for name,num,den in [('logo_churn_rate','churned_customers','beginning_customers'),('gross_revenue_churn','churned_mrr','beginning_mrr'),('arpa','active_mrr','active_customers')]:
        monthly[name]=monthly[num]/monthly[den].replace(0,np.nan)
    monthly['customer_retention_rate']=1-monthly.logo_churn_rate
    monthly['gross_revenue_retention']=1-monthly.gross_revenue_churn
    monthly['arr']=12*monthly.active_mrr
    monthly.to_csv(OUT/'monthly_saas_metrics.csv',index=False)
    c['tenure_days']=(c.ended_at.fillna(AS_OF)-c.started_at).dt.days
    c['tenure_bucket']=pd.cut(c.tenure_days,[-1,90,180,365,730,10000],labels=['0–3 months','3–6 months','6–12 months','12–24 months','24+ months']).astype(str)
    c.to_csv(OUT/'customer_analytics.csv',index=False)
    risk=c.merge(billing_features(data,AS_OF).drop(columns=['account_id','mrr']),on='subscription_id')
    risk=risk[(risk.started_at<=AS_OF)&(risk.ended_at.isna()|(risk.ended_at>AS_OF))].sort_values(['risk_flag','mrr'],ascending=False)
    risk.to_csv(OUT/'billing_risk_accounts.csv',index=False)
    calendar=pd.DataFrame({'date':pd.date_range('2023-01-01',AS_OF)})
    calendar['year']=calendar.date.dt.year;calendar['quarter']='Q'+calendar.date.dt.quarter.astype(str)
    calendar['month']=calendar.date.dt.strftime('%b');calendar['month_number']=calendar.date.dt.month
    calendar['month_year']=calendar.date.dt.strftime('%b %Y');calendar['year_month_sort']=calendar.date.dt.year*100+calendar.date.dt.month
    calendar['month_start']=calendar.date.dt.to_period('M').dt.to_timestamp();calendar['month_end']=calendar.date+pd.offsets.MonthEnd(0)
    calendar['week']=calendar.date.dt.isocalendar().week.astype(int)
    calendar.to_csv(OUT/'dim_date.csv',index=False)
    # Separate facts with conformed account/plan keys; never join attempts directly to sums of invoices.
    inv=data['invoices'].merge(c[['subscription_id','account_id','plan_id']],on='subscription_id',validate='many_to_one')
    pay=data['payments'].merge(inv[['invoice_id','subscription_id','account_id','plan_id']],on='invoice_id',validate='many_to_one')
    inv.to_csv(OUT/'fact_invoice.csv',index=False);pay.to_csv(OUT/'fact_payment.csv',index=False)
    # Lifetime billing comparison is descriptive only; predictive work uses fixed landmarks.
    lifetime=pay.groupby('account_id').agg(payment_attempts=('payment_id','size'),failed_attempts=('payment_status',lambda x:(x=='failed').sum()))
    c=c.join(lifetime,on='account_id').fillna({'payment_attempts':0,'failed_attempts':0})
    c['failure_group']=np.select([c.failed_attempts>=2,c.failed_attempts==1],['2+ failures','1 failure'],default='0 failures')
    c.groupby('failure_group').agg(accounts=('account_id','size'),churned=('status',lambda x:(x=='cancelled').sum()),mean_tenure=('tenure_days','mean')).to_csv(OUT/'lifetime_billing_churn.csv')
    conn=sqlite3.connect(':memory:')
    for name,d in {**data,'customer_analytics':c,'subscription_monthly_snapshot':snap,'monthly_saas_metrics':monthly,'billing_risk_accounts':risk,'dim_date':calendar,'fact_invoice':inv,'fact_payment':pay}.items():
        d.to_sql(name,conn,if_exists='replace',index=False)
    return c,monthly,conn

if __name__=='__main__':
    build(load())
