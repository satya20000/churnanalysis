-- Descriptive tenure at cancellation, not exposure-adjusted hazard.
SELECT tenure_bucket,plan_name,COUNT(*) AS churned_customers,SUM(mrr) AS churned_mrr,AVG(tenure_days) AS average_tenure_days
FROM customer_analytics WHERE ended_at IS NOT NULL GROUP BY tenure_bucket,plan_name;
