-- Customer distribution at account grain. Active as of the fixed coverage end.
SELECT segment, region, acquisition_channel, COUNT(*) AS accounts,
 SUM(CASE WHEN started_at <= '2025-12-31 23:59:59' AND (ended_at IS NULL OR ended_at > '2025-12-31 23:59:59') THEN 1 ELSE 0 END) AS active,
 SUM(CASE WHEN ended_at IS NOT NULL THEN 1 ELSE 0 END) AS cancelled
FROM customer_analytics GROUP BY segment, region, acquisition_channel;
