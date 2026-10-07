# Business insights — synthetic SaaS, 31 December 2025

Every figure is a result from version 1.0.0, not an industry benchmark. Monetary units are source currency units (CU); the publisher does not specify a currency.

1. **Recurring revenue:** 4,035 active accounts contribute CU 1,387,441 MRR and CU 16,649,292 annualized run rate. December logo churn is 1.08%; gross revenue churn is 0.97%.
2. **Concentration:** Enterprise contributes CU 558,069, or 40.2% of active MRR. Its 223 active accounts represent 5.5% of customers.
3. **Acquisition coverage:** no subscription starts occur in November or December 2025. MRR falls from CU 1,417,797 in October to CU 1,387,441 in December (-2.14%). This cannot establish an acquisition failure: the source stops starts in October.
4. **Exposure-adjusted segment churn:** highest pooled monthly logo churn is SMB at 1.22% per account-month of beginning exposure. mid_market accounts contribute the largest cumulative cancellation MRR: CU 137,271. Pooled rates are ratios of sums, not averages of percentages.
5. **Billing:** lifetime attempt failure rate is 8.23%. Successful collections are CU 27,639,401, 93.70% of non-void invoice value. This is a cash collection ratio, not recognized revenue.
6. **Priority queue:** 1,165 active accounts with recent failures/retries or matured overdue balances represent CU 396,533 MRR (28.6%). This is an analytical indicator, not expected or contractual loss.
7. **Prospective billing signal:** among eligible accounts active at 30 September, churn over the next 90 days is 0 failures: 125/3594 (3.48%); 1 failure: 11/338 (3.25%). Zero denominators and small groups must not be interpreted as strong evidence. The fixed-landmark comparison controls the observation window but is not adjusted for plan, segment or tenure.
8. **Cohort maturity:** 24 cohorts have observable month-12 retention. Weighted retention is 86.90%. Newer cohorts remain blank for unobservable ages.

## Recommendations

- Finding: Enterprise supplies 40.2% of MRR. Implication: losing a small number of these accounts can materially affect revenue. Action: route the highest-MRR risk accounts to an account owner; monitor recovery and retention separately.
- Finding: 1,165 accounts meet the transparent priority definition. Implication: billing intervention has an identifiable queue. Action: validate balances, retry eligible failures and track recovered cash; evaluate a controlled dunning pilot before attributing retention gains.
- Finding: every non-void December invoice is open and no December invoice has a successful payment. Implication: terminal-month collection and open balances reflect a source-boundary anomaly. Action: treat December collection as provisional and request settlement/void event history before estimating actual loss.
- Finding: November and December have no subscription starts. Implication: the final MRR decline is mathematically cancellation-driven, while the acquisition interpretation is uncertain. Action: confirm source completeness before changing channel budgets.
- Finding: highest exposure-normalized churn is SMB. Implication: customer counts and revenue exposure call for different priorities. Action: test segment onboarding improvements and compare matched cohorts; do not reallocate budgets from raw historical cancellation fractions.

## Evidence

Reproduce with `python src/run_analysis.py`. Figures trace to `data/processed/executive_summary.json`, monthly marts, `segment_exposure_churn.csv`, `landmark_billing_churn.csv` and `cohort_retention.csv`. `09_pre_cancellation_failures.csv` describes pre-cancellation events; lifetime groups are descriptive and exposure-confounded. Predictive classifier omitted because signal investigation is sufficient and no stronger claim is warranted.
