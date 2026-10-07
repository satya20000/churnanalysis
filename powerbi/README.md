# Open the report on Windows

1. Clone/download the entire repository; do not move the `powerbi` directory away from `data`.
2. In PowerShell, run `powershell -ExecutionPolicy Bypass -File .\powerbi\Set-ProjectPath.ps1`. This changes only the local model source path.
3. Open `powerbi/SaaS_Churn_Revenue_Intelligence.pbip` in current Power BI Desktop. Enable Power BI Projects if your Desktop version requires it.
4. Select **Refresh**. File-source privacy/permissions may need local approval. There are no credentials or cloud data sources in this project.
5. Import `powerbi/theme.json` from View → Themes → Browse for themes.
6. Mark DimDate as the date table using its `date` column. `month_year` and month names already specify chronological sort columns.
7. Verify the native QA checklist in `docs/qa_report.md`. Default date scope includes all history; MRR/active/risk use the latest selected snapshot; flow churn rates use the selected period's summed exposure. Select Dec 2025 for the December executive figures.
8. For cohort heatmap colors, apply background conditional formatting to Cohort Retention: sequential palette from 0 to 1, blanks unformatted. Monthly dates do not filter the cohort matrix; plan/segment/region/channel do.
9. In Billing, choose one landmark (recommended 30 Sep 2025). This selector is independent of the date slicer. Priority table is explicitly a 31 Dec 2025 queue, while the MRR-at-risk card uses the selected month's snapshot.
10. Sort the cancellation account table by Churned MRR descending and the priority table by Latest Priority MRR descending. Exclude blank measure rows if your Desktop visual shows them. Save as `.pbix` and capture native screenshots after these checks pass.

## Status and format

PBIP uses documented enhanced PBIR page/visual JSON and a TMSL `model.bim`, with a relative report-to-model binding. This environment runs Linux and has no Power BI Desktop or DAX engine. Report/model files are authored, not natively accepted. A native `.pbix` cannot honestly be produced or verified here. Static PNGs are reproducible Python analytical previews.

No current source statuses are used for historical active MRR. FactMonthlySnapshot is account-month grain with separate beginning, ending, acquisition and cancellation quantities. Account and plan dimensions filter all facts directly, with no fact-to-fact joins that multiply invoice value by payment retry count.

One-day date selections represent that day for invoices/payments and only matching month-end rows for subscription snapshots; use **Month** for a consistent monthly report. A snapshot-only period with no rows returns blank rather than zero. Month-end comparisons use the complete calendar month. Customer rates over multiple months are pooled exposure rates, not compounded retention.

The report provides the required analytical views. Native visual polish, matrix conditional formatting, exact chart sort behavior and screenshot acceptance remain explicitly pending in Desktop. Microsoft format documentation: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report and https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset.

The monthly account snapshot is stored as lossless CSV gzip (`subscription_monthly_snapshot.csv.gz`). Power Query decompresses it automatically; the Python pipeline regenerates both forms.
