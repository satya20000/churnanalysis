# Methodology and analytical limits

## Evidence and lineage

Original CSV release from Analytics Engineering v1.0.0 → preserved raw CSVs → source-profile/quality assertions → conformed subscription-month, invoice/payment and account/cohort marts → executed SQL outputs → Python findings → PBIR report/TMSL model. SHA-256 checksums and original license identify the exact release. `python src/run_analysis.py` rebuilds the pipeline and figures.

The source has 5,000 accounts, 4 plans, 5,000 subscription periods, 85,448 invoices and 87,287 attempts. No product-usage events exist. Preserve literal `NA` as a region. Missing end dates are right-censoring, not missing labels. Dates are date-only; no intraday timing or time zone conversion is inferred.

## Modeling

The source relationship chain is accounts 1:* subscriptions, plans 1:* subscriptions, subscriptions 1:* invoices and invoices 1:* payments. This release has one subscription per account. In the analytical model, invoice and payment facts each carry account/plan keys for direct dimension filtering. Do not connect facts bidirectionally or sum invoice value after a retry-level join.

FactMonthlySnapshot is 5,000 × 36 rows. Keeping inactive rows preserves start/end event quantities for every slicer dimension. Balances select the latest month; flow quantities sum over selected months. DimDate has daily rows, calendar labels and numerical chronological sorts. Cohort facts retain account identifiers, avoiding incorrectly averaging aggregated retention percentages when filtering.

## Cohorts and survival

Subscription start defines acquisition month. Evaluate at the end of each age month. Retention denominator is the original cohort, including early cancellations; month 0 is observed end-of-month persistence. Future ages remain NULL; the account-grain Power BI fact omits unobservable rows. The Python output retains their NULL cells to make right-censoring visible.

Kaplan–Meier multiplies (1 − events/at-risk) across event days. Accounts still active at 2025-12-31 are censored. Tied censor/event days keep censoring accounts at risk through that day. Greenwood log-log 95% intervals are calculated; survival is descriptive and assumes independent censoring. Immutable plan/segment/acquisition-channel curves avoid future-risk classification. `landmark_survival.csv` conditions on surviving to 30 Sep 2025 and groups using billing history before that date, avoiding immortal-time bias from an ever-failed label at subscription start.

## Billing signals and leakage prevention

Six fixed quarterly landmarks cover Jun 2024–Sep 2025. Eligibility requires active subscription and ≥30 days tenure. Features use event rows dated at/before landmark; recent failures/retries use the prior 30 days. Outcome is cancellation in following 90 days. The horizon is complete for all landmarks. Feature construction does not use future ended_at/status as a predictor, final invoice_status, future attempts or future tenure. End dates are used solely to define eligibility and outcome.

Historical overdue balances reconstruct amount_due minus successes available at landmark and require due date at least 30 days earlier. Void transition dates are unknown; reconstructed unpaid exposure may include an obligation later voided. This proxy is labeled, not treated as a contractual receivable balance. MRR at risk is an account-level indicator, not a churn probability, loss estimate or provision.

The comparison reports event counts, denominators and absolute 90-day risks. Zero/missing groups are not invented. The 30-day window in this release produces no 2+ failure group at the September landmark; absence is stated rather than replaced with a fictional rate. Accounts can recur across landmarks, so pooled rows cannot be treated as independent observations. Lifetime failures versus churn are also exported but expressly confounded by varying exposure time.

No classifier is built: it is optional in the brief, and the fixed-window signal investigation is the primary decision evidence. A future model should use disjoint account groups and complete prospective horizons, temporal holdout, frozen feature windows and explicit calibration. No machine-learning accuracy is claimed.

## Interpretation

December has only open/void invoices and no successful payment for a December invoice; November/December have no starts. These data-generation/coverage features must be validated before a real-world intervention interpretation. Channel budgets cannot be optimized from this dataset without acquisition spend, CAC, margins and matched tenure. No causal billing effect is estimated.

The monthly account snapshot is stored as lossless CSV gzip (`subscription_monthly_snapshot.csv.gz`). Power Query decompresses it automatically; the Python pipeline regenerates both forms.
