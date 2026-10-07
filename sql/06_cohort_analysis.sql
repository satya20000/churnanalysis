-- Observable month-end cohort retention; future cells are NULL, never zero.
WITH RECURSIVE ages(age_months) AS (SELECT 0 UNION ALL SELECT age_months+1 FROM ages WHERE age_months<35),
cohort_accounts AS (SELECT *,date(started_at,'start of month') AS cohort FROM subscriptions),
expanded AS (SELECT c.*,a.age_months,date(cohort,'+'||a.age_months||' months','+1 month','-1 day') AS observation_date FROM cohort_accounts c CROSS JOIN ages a)
SELECT cohort,age_months,COUNT(*) AS cohort_size,
 CASE WHEN observation_date<='2025-12-31' THEN SUM(CASE WHEN ended_at IS NULL OR date(ended_at)>observation_date THEN 1 ELSE 0 END) END AS retained,
 CASE WHEN observation_date<='2025-12-31' THEN SUM(CASE WHEN ended_at IS NULL OR date(ended_at)>observation_date THEN 1 ELSE 0 END)*1.0/COUNT(*) END AS retention
FROM expanded GROUP BY cohort,age_months ORDER BY cohort,age_months;
