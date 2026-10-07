"""Starter profile for SaaS Subscriptions & Customer Churn Dataset."""
import sqlite3
from pathlib import Path

database = next(Path(".").glob("*.sqlite"))
with sqlite3.connect(database) as connection:
    query = """SELECT p.plan_name,
       COUNT(*) AS active_subscriptions,
       ROUND(SUM(s.mrr), 2) AS current_mrr
FROM subscriptions s
JOIN plans p USING (plan_id)
WHERE s.status = 'active'
GROUP BY p.plan_name
ORDER BY current_mrr DESC;"""
    rows = connection.execute(query).fetchall()
    for row in rows:
        print(row)
