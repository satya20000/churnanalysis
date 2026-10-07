# Metric dictionary

Source: synthetic v1.0.0. Reporting cutoff: 2025-12-31. Date-only lifecycle: started_at is inclusive; ended_at is exclusive. Monetary unit CU (currency unspecified). Monthly snapshot grain is one account × one calendar month; the source guarantees one subscription per account. Rates below return blank when their denominator is zero.

| Metric | Definition and reporting behavior |
|---|---|
| Beginning customers | Started before first day of month, no end or ended on/after first day; exposure immediately before the boundary |
| Active customers | Started by month-end, no end or ended strictly after month-end; latest selected month |
| New customers | Subscription started within month, including any that cancel in same month |
| Churned customers | ended_at within month; includes same-month entrants if present |
| Logo churn | Monthly churned customers / beginning customers; selected multi-month scope is summed cancellations / summed beginning exposures |
| Customer retention | 1 − logo churn; monthly convention, not compounded multi-month retention |
| MRR | Sum of contracted mrr active at month-end; latest selected snapshot, never sum monthly balances |
| ARR | MRR × 12; annualized run rate, not accounting revenue |
| Beginning MRR | Contracted mrr of beginning customers |
| New MRR | mrr of subscription starts within period |
| Churned MRR | mrr of terminations within period |
| Gross revenue churn | Churned MRR / beginning MRR; ratio of sums across months |
| Gross revenue retention | 1 − gross revenue churn; cancellation-only proxy; contraction unavailable |
| ARPA | Ending MRR / ending active customers |
| Average churn tenure | Sum of days from start to end for selected cancellations / selected cancellations |
| Invoiced value | Sum invoices.amount_due; invoice date scope; report void amount separately |
| Paid invoice value | Invoice value with final invoice_status=paid; final classification, not historical paid-as-of date |
| Collected value | Sum amount of succeeded attempts, by attempted_at; each success counted once; failed attempts are never revenue |
| Collection rate | Lifetime successful collection / lifetime non-void invoice value; payment/invoice date windows differ, so do not compare two arbitrary monthly windows as a reconciled collection ratio |
| Open invoice value | Invoice value with final invoice_status=open; invoice date cohort, not historical status timeline |
| Failed attempts | Payment rows with payment_status=failed |
| Failed payment rate | Failed attempts / total attempts; attempts, not invoices or customers |
| Accounts with failures | Distinct account keys with failed attempt(s) in selected attempted_at scope |
| Payment attempts per invoice | All attempt count / all invoice count, including zero-attempt invoices |
| Historical mature unpaid balance | Invoice billed by cutoff and due ≥30 days before cutoff, less succeeded payment value available by cutoff, floored at zero; no future final status used |
| MRR at Risk | Ending MRR for active accounts with ≥1 failure in past 30 days, ≥1 invoice with multiple attempts in past 30 days, or ≥1 mature unpaid invoice at cutoff; once per account |
| Risk accounts | Active accounts meeting the same indicator at latest selected month |
| Latest priority MRR | Same account queue at 31 Dec 2025, independent of report date slicer |
| Cohort retention | Accounts from subscription-start month still active at observed age's month-end / original cohort size; month 0 is end-of-acquisition-month survival, not forced to 100% |
| Landmark churn 90d | Among accounts started ≥30 days ago and still active on landmark: cancelled in next 90 days / eligible accounts; payment signals only from history at landmark |
| High-value cancellations | Account identifiers sorted by cancellation MRR; top of ranking, no invented monetary threshold |
| Revenue concentration | Active MRR in segment/plan / total active MRR at same month-end |

## Important boundaries

Monthly bridges: ending customers = beginning + starts − ends; ending MRR = beginning + new − cancelled MRR. Rate convention follows the brief's all-cancellation numerator; if a same-month entrant cancels, the rate is not an exact beginning-population survival probability. Separate bop_churned_customers and bop_churned_mrr are supplied to support strict beginning-population variants. No same-month cancellations were found in this release.

Historical unpaid balances are an event-based analytical signal. Void/status-change dates are unavailable, so obligations later voided cannot reliably be removed at an earlier cutoff. At year-end, final-status open value is reported separately from reconstructed mature balances. Non-void December invoices are all open; the 30-days-overdue criterion keeps that source-boundary pattern from flagging every account.

No true NRR, expansion, contraction, reactivation or upsell is calculated. Historical plan changes and returning subscription events are absent. Churn associations do not prove causation. Pooled account-month/landmark exposures are not independent person counts.
