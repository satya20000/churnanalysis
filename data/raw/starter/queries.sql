-- SaaS Subscriptions & Customer Churn Dataset starter queries
-- Checked against the v1.0.0 SQLite release.
-- Question: How much current MRR comes from each active plan?
SELECT p.plan_name,
       COUNT(*) AS active_subscriptions,
       ROUND(SUM(s.mrr), 2) AS current_mrr
FROM subscriptions s
JOIN plans p USING (plan_id)
WHERE s.status = 'active'
GROUP BY p.plan_name
ORDER BY current_mrr DESC;

-- Basic exploration:
SELECT COUNT(*) AS row_count
FROM plans;

SELECT *
FROM plans
LIMIT 20;
