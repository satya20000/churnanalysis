-- Monthly exposure denominators, sliceable by all account dimensions and plan.
SELECT f.month_start, c.plan_name, c.segment, c.region, c.acquisition_channel,
 SUM(f.beginning_customers) AS beginning_customers,
 SUM(f.new_customers) AS new_customers, SUM(f.churned_customers) AS churned_customers,
 SUM(f.active_customers) AS active_customers,
 1.0*SUM(f.churned_customers)/NULLIF(SUM(f.beginning_customers),0) AS logo_churn_rate,
 SUM(f.churned_tenure_days)*1.0/NULLIF(SUM(f.churned_customers),0) AS average_churn_tenure_days
FROM subscription_monthly_snapshot f JOIN customer_analytics c USING(subscription_id)
GROUP BY f.month_start,c.plan_name,c.segment,c.region,c.acquisition_channel;
