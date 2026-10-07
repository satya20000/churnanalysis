# QA and completion status

## Executed

- Source key uniqueness, required fields, duplicates, all FK integrity checks and one-subscription-per-account assertion.
- Lifecycle ordering/status agreement, positive numeric values, due-date ordering and payment dates after billing.
- Paid invoice amounts equal successful payment value; successful invoice collections never exceed due amount.
- Nine SQL files executed against the rebuilt in-memory SQLite model.
- Independent raw-table SQL MRR calculations match Python for all 36 months.
- SQL/Python cohort retention matches including NULL future cells.
- Monthly customer and MRR bridges reconcile.
- Python-generated previews and cohort/survival figures inspected.
- Notebook code cells executed in a fresh Python process through IPython; real stdout and rich displays captured. Native Jupyter TCP/IPC kernel binds are blocked by the host. Notebook remains compatible with normal Jupyter on a workstation.
- Power BI model field/relation references, dimension uniqueness, visual field references, DAX measure names and page geometry checked programmatically.
- PBIR schema validation status recorded by `src/verify_project.py` in `data/processed/validation_receipt.json`.

## Power BI Desktop checks pending

Linux does not provide Power BI Desktop or its model/DAX execution engine. No PBIX export or native screenshots have been produced. Python images are analytical previews. These remaining checks must be run before describing the native report as production-accepted:

- Open PBIP and refresh every M partition with a configured ProjectRoot.
- Verify Dec 2025: active customers 4,035; MRR CU 1,387,441; cancelled customers 44; cancelled MRR CU 13,594; churn 1.0787%; gross retention 99.0297%.
- Check representative plan/segment/channel/region selections, then clear to All; recompute numerator and exposure, never average rates.
- Verify latest-month balance behavior and multi-month pooled flow rates.
- Validate cross-filter interactions among chart marks and tables; FactMonthlySnapshot and source facts must filter through conformed dimensions.
- Apply sequential conditional formatting to cohort matrix; confirm unobservable cells stay blank and date-slicer scope is clear.
- Confirm month-year chronological order and category labels; no unintended blanks.
- Choose one landmark, compare 0/1 failures, validate denominator counts and complete horizon. September: 3,594/125 versus 338/11.
- Priority account queue stays at 31 Dec 2025 and is labeled as such; history-sensitive MRR at Risk follows the selected month.
- Check currency CU, percent formats, tooltip values, card display units, labels, narrow-window rendering, text overlap and page navigation.
- Apply theme; sort high-value and priority queues; export PBIX and native screenshots.

The repository is an executed analytical project with an authored Power BI deliverable. It is not represented as a natively verified Power BI report.
