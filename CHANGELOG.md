## Unreleased

### Feat

- **bi**: add Docker Compose local Superset runtime
- **bi**: assemble P4-01-P4-07 charts into one dashboard + FR-7 filters [P4-08]
- **bi**: add top-5-cities chart for question d [P4-05]
- **bi**: question a -- orders/qty/value sliced and filtered [P4-02]
- **bi**: add question-b top-products-by-AOV chart + dataset [P4-03]
- **bi**: question-f chart + Promotion-impact hero KPI [P4-07]
- **bi**: add question-c top-10-customers chart [P4-04]
- **bi**: add question-e time-series chart (orders/qty/value by month & year) [P4-06]
- **eda**: add notebooks/eda.ipynb — product mix, channel, geography, promotion [P4-09]
- **bi**: add Superset-as-code scaffold + hero KPI tiles [P4-01]
- **fact**: build fct_sales at order-line grain over all channels [P3-03]
- **dims**: rework dim_customer and dim_credit_card for all-channel scope [P3-05]
- **marts**: add bridge_order_sales_reason mart [P3-02]
- **sources**: load canonical AdventureWorks to DuckDB Parquet source [P3-01] (#11)
- **dims**: add dim_order_status with PK and relationships test [P2-07] (#10)
- **dims**: add dim_sales_reason with PK and not-null tests [P2-06] (#9)
- **dims**: add dim_credit_card with PK and accepted-values tests [P2-05] (#8)
- **dims**: add dim_date via dynamic date_spine with gap-free test [P2-04] (#7)
- **dims**: add dim_customer with PK and data-quality tests [P2-03] (#6)
- **dims**: add dim_product with PK and data-quality tests [P2-02] (#5)
- **dims**: add dim_geography with PK and data-quality tests [P2-01] (#4)
- **sources**: seed adventure_works fixtures and declare source [P1-02] (#2)

### Fix

- **bi**: rename dashboard outer test to satisfy test-path convention [P4-08]
- **bi**: correct table alias in direct-aggregate oracle SQL [P4-05]
- **bi**: rename outer test script to satisfy test-path convention [P4-04]
- **fact**: correct P3-04 promotion-reason literal in bridge invariant test [P3-04]
- update .sdd profile

### Refactor

- **layout**: move dbt project into transform/, add notebooks/ bi/ data/
- **layout**: move dbt project into transform/, add notebooks/ and bi/
