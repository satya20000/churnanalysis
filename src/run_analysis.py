"""One-command reproducible build, independent SQL reconciliation and evidence output."""
import json, sqlite3
import numpy as np
import pandas as pd
from data_processing import ROOT,OUT,AS_OF,load,build
from cohort_analysis import cohorts,survival
from churn_analysis import signals

def run():
    data=load();c,m,conn=build(data);co=cohorts(c);sv=survival(c);f,lc=signals(data,c)
    lc.to_sql('landmark_billing_churn',conn,if_exists='replace',index=False)
    co.to_sql('cohort_retention',conn,if_exists='replace',index=False)
    results={}
    for file in sorted((ROOT/'sql').glob('*.sql')):
        r=pd.read_sql_query(file.read_text(),conn);r.to_csv(OUT/(file.stem+'.csv'),index=False);results[file.stem]=r
    rawsql=results['04_mrr_analysis']
    for col in ['beginning_mrr','active_mrr','churned_mrr','new_mrr']:
        assert np.allclose(rawsql[col],m[col]),col
    sqlco=results['06_cohort_analysis']
    assert np.allclose(sqlco.retention,co.sort_values(['cohort','age_months']).retention,equal_nan=True)
    assert (m.active_customers==m.beginning_customers+m.new_customers-m.churned_customers).all()
    assert np.allclose(m.active_mrr,m.beginning_mrr+m.new_mrr-m.churned_mrr)
    assert results['01_data_quality'].violations.sum()==0
    conn.close()
    risk=pd.read_csv(OUT/'billing_risk_accounts.csv');last=m.iloc[-1]
    a=c[c.ended_at.isna()]
    latest=lc[lc.landmark==pd.Timestamp('2025-09-30')].copy()
    denom=data['invoices'].loc[data['invoices'].invoice_status!='void','amount_due'].sum()
    collected=data['payments'].loc[data['payments'].payment_status=='succeeded','amount'].sum()
    stats={'as_of':'2025-12-31','accounts':len(c),'active_customers':int(last.active_customers),'cancelled':int(c.ended_at.notna().sum()),'mrr':float(last.active_mrr),'arr':float(last.arr),'dec_logo_churn':float(last.logo_churn_rate),'dec_gross_revenue_churn':float(last.gross_revenue_churn),'dec_churned_mrr':float(last.churned_mrr),'arpa':float(last.arpa),'risk_mrr':float(last.mrr_at_risk),'risk_accounts':int(last.risk_accounts),'failed_payment_rate':float((data['payments'].payment_status=='failed').mean()),'open_invoice_value':float(data['invoices'].loc[data['invoices'].invoice_status=='open','amount_due'].sum()),'collected_value':float(collected),'collection_rate':float(collected/denom),'total_invoiced':float(data['invoices'].amount_due.sum()),'churned_mrr_all':float(c.loc[c.ended_at.notna(),'mrr'].sum()),'avg_churn_tenure_days':float(c.loc[c.ended_at.notna(),'tenure_days'].mean()),'plan_active_mrr':a.groupby('plan_name').mrr.sum().to_dict(),'landmark_sept':latest.drop(columns='landmark').to_dict('records'),'sql_reconciliation':'passed','bridge_checks':'passed'}
    (OUT/'executive_summary.json').write_text(json.dumps(stats,indent=2))
    findings(c,m,co,lc,stats)
    from render_assets import render
    render(c,m,co,sv,lc,data,stats)
    print(json.dumps(stats,indent=2))
    return stats

def findings(c,m,co,lc,s):
    a=c[c.ended_at.isna()];plan=max(s['plan_active_mrr'],key=s['plan_active_mrr'].get)
    ch=c[c.ended_at.notna()];seg=ch.groupby('segment').mrr.sum().sort_values(ascending=False)
    exposure=pd.read_csv(OUT/'subscription_monthly_snapshot.csv').merge(c[['account_id','segment','acquisition_channel','plan_name','region']],on='account_id')
    seg_churn=exposure.groupby('segment')[['beginning_customers','churned_customers']].sum();seg_churn['rate']=seg_churn.churned_customers/seg_churn.beginning_customers.replace(0,np.nan)
    seg_churn.to_csv(OUT/'segment_exposure_churn.csv')
    channels=co[co.age_months==12].dropna(subset=['retention'])
    riskpct=s['risk_mrr']/s['mrr']
    latest=lc[lc.landmark==pd.Timestamp('2025-09-30')]
    comparison='; '.join(f"{r.risk_group}: {r.churned}/{r.accounts} ({r.churn_90d:.2%})" for _,r in latest.iterrows())
    insights=f'''# Business insights — synthetic SaaS, 31 December 2025

Every figure is a result from version 1.0.0, not an industry benchmark. Monetary units are source currency units (CU); the publisher does not specify a currency.

1. **Recurring revenue:** {s['active_customers']:,} active accounts contribute CU {s['mrr']:,.0f} MRR and CU {s['arr']:,.0f} annualized run rate. December logo churn is {s['dec_logo_churn']:.2%}; gross revenue churn is {s['dec_gross_revenue_churn']:.2%}.
2. **Concentration:** {plan} contributes CU {s['plan_active_mrr'][plan]:,.0f}, or {s['plan_active_mrr'][plan]/s['mrr']:.1%} of active MRR. Its {len(a[a.plan_name==plan])} active accounts represent {len(a[a.plan_name==plan])/len(a):.1%} of customers.
3. **Acquisition coverage:** no subscription starts occur in November or December 2025. MRR falls from CU {m.iloc[-3].active_mrr:,.0f} in October to CU {s['mrr']:,.0f} in December ({s['mrr']/m.iloc[-3].active_mrr-1:.2%}). This cannot establish an acquisition failure: the source stops starts in October.
4. **Exposure-adjusted segment churn:** highest pooled monthly logo churn is {seg_churn.rate.idxmax()} at {seg_churn.rate.max():.2%} per account-month of beginning exposure. {seg.index[0]} accounts contribute the largest cumulative cancellation MRR: CU {seg.iloc[0]:,.0f}. Pooled rates are ratios of sums, not averages of percentages.
5. **Billing:** lifetime attempt failure rate is {s['failed_payment_rate']:.2%}. Successful collections are CU {s['collected_value']:,.0f}, {s['collection_rate']:.2%} of non-void invoice value. This is a cash collection ratio, not recognized revenue.
6. **Priority queue:** {s['risk_accounts']:,} active accounts with recent failures/retries or matured overdue balances represent CU {s['risk_mrr']:,.0f} MRR ({riskpct:.1%}). This is an analytical indicator, not expected or contractual loss.
7. **Prospective billing signal:** among eligible accounts active at 30 September, churn over the next 90 days is {comparison}. Zero denominators and small groups must not be interpreted as strong evidence. The fixed-landmark comparison controls the observation window but is not adjusted for plan, segment or tenure.
8. **Cohort maturity:** {len(channels)} cohorts have observable month-12 retention. Weighted retention is {channels.retained.sum()/channels.cohort_size.sum():.2%}. Newer cohorts remain blank for unobservable ages.

## Recommendations

- Finding: {plan} supplies {s['plan_active_mrr'][plan]/s['mrr']:.1%} of MRR. Implication: losing a small number of these accounts can materially affect revenue. Action: route the highest-MRR risk accounts to an account owner; monitor recovery and retention separately.
- Finding: {s['risk_accounts']:,} accounts meet the transparent priority definition. Implication: billing intervention has an identifiable queue. Action: validate balances, retry eligible failures and track recovered cash; evaluate a controlled dunning pilot before attributing retention gains.
- Finding: every non-void December invoice is open and no December invoice has a successful payment. Implication: terminal-month collection and open balances reflect a source-boundary anomaly. Action: treat December collection as provisional and request settlement/void event history before estimating actual loss.
- Finding: November and December have no subscription starts. Implication: the final MRR decline is mathematically cancellation-driven, while the acquisition interpretation is uncertain. Action: confirm source completeness before changing channel budgets.
- Finding: highest exposure-normalized churn is {seg_churn.rate.idxmax()}. Implication: customer counts and revenue exposure call for different priorities. Action: test segment onboarding improvements and compare matched cohorts; do not reallocate budgets from raw historical cancellation fractions.

## Evidence

Reproduce with `python src/run_analysis.py`. Figures trace to `data/processed/executive_summary.json`, monthly marts, `segment_exposure_churn.csv`, `landmark_billing_churn.csv` and `cohort_retention.csv`. `09_pre_cancellation_failures.csv` describes pre-cancellation events; lifetime groups are descriptive and exposure-confounded. Predictive classifier omitted because signal investigation is sufficient and no stronger claim is warranted.
'''
    (ROOT/'docs/business_insights.md').write_text(insights)
    (ROOT/'docs/data_quality_summary.md').write_text('# Data quality\n\nAll '+str(len(pd.read_csv(OUT/'quality_checks.csv')))+' ingestion assertions passed, plus independent SQL foreign-key checks, 36 monthly raw-lifecycle reconciliations and customer/MRR bridge checks.\n\n`NA` is a valid region code, preserved with `keep_default_na=False`; empty ended_at is a valid censoring value.\n\nCritical interpretation issues: all non-void December invoices are open, no December invoice collections; no starts after October. These are source observations, not evidence of a real business deterioration. Final invoice status cannot reconstruct historical open status; historical balances use payment events without future statuses. Void-event dates are absent, so mature unpaid balances may include later-void obligations.\n\nSee quality_checks.csv and source_profile.json for dimensions, types, nulls, categories, numeric distributions and dates.')
    (ROOT/'README.md').write_text(f'''# SaaS Revenue Retention & Churn Intelligence

**End-to-end B2B SaaS analytics using SQL, Python and a Power BI project**
By Satya Ranjan Nayak · MBA, IBS Hyderabad (2026–2028)

![Executive analytical preview](assets/executive_dashboard.png)

## Business problem

Management needs to distinguish subscription growth, cancellation losses and cash collection. This project models customer exposure over time, compares acquisition cohorts and tests whether payment friction precedes churn. It turns those results into a prioritized account queue and transparent executive metrics.

## Executive summary

- **{s['active_customers']:,} active customers · CU {s['mrr']:,.0f} MRR · CU {s['arr']:,.0f} ARR run rate.**
- December logo churn **{s['dec_logo_churn']:.2%}**, gross revenue retention **{1-s['dec_gross_revenue_churn']:.2%}**.
- {plan} contributes **{s['plan_active_mrr'][plan]/s['mrr']:.1%}** of active MRR.
- **CU {s['risk_mrr']:,.0f}** MRR across **{s['risk_accounts']:,}** priority billing-risk accounts.
- **Source limitation identified:** terminal Non-void December invoices are all open; no starts occur after October. These caveats prevent a misleading performance story.

See [eight quantified findings and five recommendations](docs/business_insights.md). All data are **synthetic educational data**, not industry benchmarks.

## Dashboard

Three report pages: Executive SaaS Overview, Customer Retention Intelligence, Billing Health & Revenue at Risk. Plan, segment, region and channel dimensions filter conformed facts; monthly snapshot facts supply time-correct MRR and beginning exposure. A cohort fact preserves account-level weighting and censoring.

**Delivery status:** editable `.pbip` / PBIR report and `model.bim` semantic model are included. Power BI Desktop is unavailable in this Linux environment: native refresh, DAX engine evaluation, slicer/cross-filter acceptance and `.pbix` export are **pending**. PNGs are Python-rendered analytical previews, not Power BI screenshots. Do not mistake static previews or JSON schema checks for native report acceptance.

[Open Power BI instructions](powerbi/README.md) · [Retention preview](assets/retention_dashboard.png) · [Billing preview](assets/billing_dashboard.png)

## Data model

![Analytical model](assets/data_model.png)

DimAccount and DimPlan have single-direction 1:* relationships to snapshot, subscription, invoice, payment and cohort facts. DimDate filters monthly snapshots on month_end, invoices on invoice_date and payments on attempted_at. Cohorts use their own cohort/age axes. No invoice–payment fact relationship is used for sums, preventing retry fanout. The source chain is documented separately.

## KPI definitions

Logo churn = cancellations during month / accounts active immediately before month start. MRR = active contracted monthly value at month-end. ARR = 12 × MRR, an annualized run rate. Gross revenue retention = 1 − cancelled MRR / beginning MRR. Collection = successful payment value / non-void invoice value. [Full dictionary](docs/metric_definitions.md).

## SQL and Python

Nine modular SQL files cover customer distributions, exposure-based churn, independent raw-lifecycle MRR, billing reconciliation, cohorts, tenure, concentration and pre-churn failures. `run_analysis.py` executes every SQL file and compares SQL results against Python.

Python builds monthly marts, validates keys and payment consistency, produces weighted cohort retention and Kaplan–Meier curves with Greenwood intervals, and tests fixed-landmark billing signals. Historical invoice statuses are excluded from predictors. No optional classifier or fabricated NRR is presented.

## How to run

```bash
git clone https://github.com/satya20000/churnanalysis.git
cd churnanalysis
python -m venv .venv
# Windows: .venv\\Scripts\\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/run_analysis.py
python src/build_powerbi.py
python src/verify_project.py
```

Open `notebooks/01_saas_churn_analysis.ipynb` for executed cells and inline figures. Hosted socket restrictions required a fresh-process IPython runner (`python src/execute_notebook.py`) instead of a Jupyter kernel; outputs come from actual cell execution. Raw CSVs are included under the source license. SQLite executes in memory to avoid host filesystem locking issues; query results are persisted as CSV.

## Repository

`data/raw` source CSVs and original license; `data/processed` reproducible marts and evidence; `sql` executed queries; `src` reusable pipeline and report generator; `notebooks` executed analysis; `powerbi` editable report/model, theme, DAX and Windows path setup; `docs` definitions/methodology/findings/QA; `assets` analytical previews and survival/cohort figures.

## Dataset, tools and limitations

Analytics Engineering, **SaaS Subscriptions & Customer Churn Dataset v1.0.0**, coverage January 2023–December 2025, **CC BY 4.0**. [Original dataset](https://www.analyticsengineering.com/datasets/saas-subscriptions). Attribution and original license are preserved in `data/raw`. Monetary amounts are **CU** because source currency is unspecified.

Tools executed: Python, pandas, NumPy, matplotlib, SQLite SQL and Git. Power BI PBIR/model/DAX authored; Desktop execution pending. No usage events, historical plan changes, reactivations or dated void/status changes are available. True NRR, expansion/contraction and causal billing effects cannot be established. Kaplan–Meier assumes independent censoring; landmark groups are observational and may be confounded. Terminal-month billing and acquisition cutoff need caution.
''')

if __name__=='__main__':run()
