-- Current operational queue. Indicator, not a forecast or contractual loss.
SELECT account_id,plan_name,segment,region,acquisition_channel,mrr,
 failed_30d,overdue_invoices,overdue_value,retried_invoices_30d,days_since_failure,risk_group
FROM billing_risk_accounts WHERE risk_flag=1 ORDER BY mrr DESC,failed_30d DESC;
