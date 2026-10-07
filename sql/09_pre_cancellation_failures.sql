-- A failure within 30 days BEFORE cancellation. Controls have a different exposure window;
-- use landmark_billing_churn.csv for a matched prospective risk comparison.
SELECT c.account_id,c.plan_name,c.mrr,c.ended_at,COUNT(p.payment_id) AS failures_30d_before_churn
FROM customer_analytics c JOIN invoices i USING(subscription_id)
JOIN payments p USING(invoice_id)
WHERE c.ended_at IS NOT NULL AND p.payment_status='failed'
 AND date(p.attempted_at)<date(c.ended_at)
 AND date(p.attempted_at)>=date(c.ended_at,'-30 days')
GROUP BY c.account_id,c.plan_name,c.mrr,c.ended_at;
