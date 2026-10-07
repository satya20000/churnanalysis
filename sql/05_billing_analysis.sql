-- Aggregate attempts BEFORE joining invoices to avoid retry-driven invoice duplication.
WITH payment_rollup AS (
 SELECT invoice_id,COUNT(*) AS attempts,
 SUM(CASE WHEN payment_status='failed' THEN 1 ELSE 0 END) AS failures,
 SUM(CASE WHEN payment_status='succeeded' THEN amount ELSE 0 END) AS collected
 FROM payments GROUP BY invoice_id
)
SELECT strftime('%Y-%m',i.invoice_date) AS invoice_month,c.plan_name,c.segment,c.acquisition_channel,
 COUNT(*) AS invoices,SUM(i.amount_due) AS invoiced_value,
 SUM(CASE WHEN i.invoice_status='paid' THEN i.amount_due ELSE 0 END) AS paid_invoice_value,
 SUM(CASE WHEN i.invoice_status='open' THEN i.amount_due ELSE 0 END) AS open_invoice_value,
 SUM(CASE WHEN i.invoice_status='void' THEN i.amount_due ELSE 0 END) AS void_invoice_value,
 SUM(COALESCE(p.collected,0)) AS collected_value,SUM(COALESCE(p.attempts,0)) AS attempts,
 SUM(COALESCE(p.failures,0)) AS failed_attempts,
 SUM(COALESCE(p.failures,0))*1.0/NULLIF(SUM(p.attempts),0) AS failed_payment_rate,
 SUM(COALESCE(p.attempts,0))*1.0/COUNT(*) AS attempts_per_invoice
FROM invoices i JOIN customer_analytics c USING(subscription_id)
LEFT JOIN payment_rollup p USING(invoice_id)
GROUP BY invoice_month,c.plan_name,c.segment,c.acquisition_channel;
