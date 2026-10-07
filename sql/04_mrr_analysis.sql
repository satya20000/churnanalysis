-- Independent raw-lifecycle computation, used to reconcile Python monthly marts.
WITH RECURSIVE months(month_start) AS (
 SELECT '2023-01-01' UNION ALL SELECT date(month_start,'+1 month') FROM months WHERE month_start<'2025-12-01'
)
SELECT month_start,
 SUM(CASE WHEN date(s.started_at)<month_start AND (s.ended_at IS NULL OR date(s.ended_at)>=month_start) THEN s.mrr ELSE 0 END) AS beginning_mrr,
 SUM(CASE WHEN date(s.started_at)<=date(month_start,'+1 month','-1 day') AND (s.ended_at IS NULL OR date(s.ended_at)>date(month_start,'+1 month','-1 day')) THEN s.mrr ELSE 0 END) AS active_mrr,
 SUM(CASE WHEN date(s.ended_at)>=month_start AND date(s.ended_at)<date(month_start,'+1 month') THEN s.mrr ELSE 0 END) AS churned_mrr,
 SUM(CASE WHEN date(s.started_at)>=month_start AND date(s.started_at)<date(month_start,'+1 month') THEN s.mrr ELSE 0 END) AS new_mrr
FROM months CROSS JOIN subscriptions s GROUP BY month_start ORDER BY month_start;
