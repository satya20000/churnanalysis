-- Independent relational checks. Every violation count must be zero.
SELECT 'orphan subscription account' AS check_name, COUNT(*) AS violations
FROM subscriptions s LEFT JOIN accounts a USING(account_id) WHERE a.account_id IS NULL
UNION ALL SELECT 'orphan plan', COUNT(*) FROM subscriptions s LEFT JOIN plans p USING(plan_id) WHERE p.plan_id IS NULL
UNION ALL SELECT 'orphan invoice', COUNT(*) FROM invoices i LEFT JOIN subscriptions s USING(subscription_id) WHERE s.subscription_id IS NULL
UNION ALL SELECT 'orphan payment', COUNT(*) FROM payments p LEFT JOIN invoices i USING(invoice_id) WHERE i.invoice_id IS NULL
UNION ALL SELECT 'end before start', COUNT(*) FROM subscriptions WHERE ended_at <= started_at
UNION ALL SELECT 'duplicate account subscription', COUNT(*) FROM (SELECT account_id FROM subscriptions GROUP BY account_id HAVING COUNT(*)>1);
