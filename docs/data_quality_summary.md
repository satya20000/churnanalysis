# Data quality

All 29 ingestion assertions passed, plus independent SQL foreign-key checks, 36 monthly raw-lifecycle reconciliations and customer/MRR bridge checks.

`NA` is a valid region code, preserved with `keep_default_na=False`; empty ended_at is a valid censoring value.

Critical interpretation issues: all non-void December invoices are open, no December invoice collections; no starts after October. These are source observations, not evidence of a real business deterioration. Final invoice status cannot reconstruct historical open status; historical balances use payment events without future statuses. Void-event dates are absent, so mature unpaid balances may include later-void obligations.

See quality_checks.csv and source_profile.json for dimensions, types, nulls, categories, numeric distributions and dates.