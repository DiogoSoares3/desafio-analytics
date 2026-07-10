# Phase 2 — Dimensions · Backlog

> Parent: [`docs/phases/phase-2/prd.md`](prd.md). Integration branch `develop`; each issue on
> `issue/<id>-<slug>`, auto-merge via gh PR. Statuses: `todo → doing → done`.
> Test command: `just build` · `just test` · `just lint`. Keys per ADR-0007; SCD Type 1 (ADR-0008).
> Each slice is vertical: source → `stg_adventure_works__*` (view) → `dim_*` (table) → schema tests + docs.

| ID | Title | Status | Blocked by |
|----|-------|--------|-----------|
| P2-01 | dim_geography (address + state + country) | todo | — |
| P2-02 | dim_product (product + subcategory + category) | todo | — |
| P2-03 | dim_customer (customer + person) | todo | — |
| P2-04 | dim_date (date_spine) | todo | — |
| P2-05 | dim_credit_card | todo | — |
| P2-06 | dim_sales_reason | todo | — |
| P2-07 | dim_order_status | todo | — |

All slices are blocked only by Phase 1 (done) and are mutually independent (conformed but no cross-dim
FK except geography, which P2-03 may reference if home-geo is included — optional, ADR-0005).

---

## P2-01 — dim_geography

### What to build
Staging views for `address`, `stateprovince`, `countryregion`, then a conformed `dim_geography` at grain
city + state/province + country (deduped), with a hashed `geography_key`. Ship-to resolution lives in the
fact (Phase 3); here we build the conformed dimension and its tests.

### Acceptance criteria
```gherkin
Scenario: dim_geography is conformed and uniquely keyed
  Given staged address, stateprovince and countryregion sources
  When I run "just build"
  Then dim_geography has one row per city + state/province + country
  And geography_key is unique and not null
  And every row has a non-null country and state/province
```
- [ ] `stg_adventure_works__address|stateprovince|countryregion` (views)
- [ ] `geography_key` via `dbt_utils.generate_surrogate_key`
- [ ] `_models.yml`: PK unique+not_null, not_null on country/state, descriptions on model + columns

### Inner loop (TDD)
`skipped — declarative SQL transform; the dbt schema tests are the acceptance gate`

### Blocked by
None - can start immediately

---

## P2-02 — dim_product

### What to build
Staging views for `product`, `productsubcategory`, `productcategory`; a `dim_product` joining them, with
`product_key`, product name/number, subcategory and category names.

### Acceptance criteria
```gherkin
Scenario: dim_product exposes product with its category hierarchy
  Given staged product, productsubcategory and productcategory sources
  When I run "just build"
  Then dim_product has one row per product with subcategory and category names
  And product_key is unique and not null
  And product_name and product_number are not null
```
- [ ] `stg_adventure_works__product|productsubcategory|productcategory` (views)
- [ ] `product_key` surrogate; category/subcategory resolved by name
- [ ] `_models.yml`: PK unique+not_null, not_null on name/number, descriptions

### Inner loop (TDD)
`skipped — declarative SQL transform; dbt schema tests are the acceptance gate`

### Blocked by
None - can start immediately

---

## P2-03 — dim_customer

### What to build
Staging views for `customer` and `person`; a `dim_customer` for **individual online customers**
(`storeid` null / person-backed), with `customer_key`, customer id, full name. Home-geography enrichment
is optional (ADR-0005) — include only if seeds link customer→address cleanly, else omit.

### Acceptance criteria
```gherkin
Scenario: dim_customer contains individual online customers
  Given staged customer and person sources
  When I run "just build"
  Then dim_customer has one row per online (person-backed) customer
  And customer_key is unique and not null
  And full_name is not null
```
- [ ] `stg_adventure_works__customer|person` (views); filter to online (storeid null)
- [ ] `customer_key` surrogate; `full_name` from person first+last
- [ ] `_models.yml`: PK unique+not_null, not_null on full_name, descriptions

### Inner loop (TDD)
`skipped — declarative SQL transform; dbt schema tests are the acceptance gate`

### Blocked by
None - can start immediately

---

## P2-04 — dim_date

### What to build
A `dim_date` generated with `dbt_utils.date_spine`, bounds computed dynamically from
`min/max(orderdate)` in staged `salesorderheader`. Day grain; attributes: date_key, year, quarter, month
number, month name, year-month, day, day-of-week, weekday/weekend flag (ADR-0006).

### Acceptance criteria
```gherkin
Scenario: dim_date is a gap-free daily calendar covering the order range
  Given staged salesorderheader with order dates
  When I run "just build"
  Then dim_date has one row per calendar day from the earliest to the latest order date
  And date_key is unique and not null
  And there are no gaps between consecutive dates
```
- [ ] `stg_adventure_works__salesorderheader` (view) providing order dates
- [ ] `date_spine` dynamic bounds; calendar attributes
- [ ] `_models.yml`: PK unique+not_null, not_null on attributes, descriptions
- [ ] singular test (or expectation) asserting no date gaps

### Inner loop (TDD)
`required` — the date-spine bound logic + gap-freeness is testable logic worth a focused test

### Blocked by
None - can start immediately

---

## P2-05 — dim_credit_card

### What to build
Staging view for `creditcard`; a `dim_credit_card` with `credit_card_key` and `card_type`.

### Acceptance criteria
```gherkin
Scenario: dim_credit_card exposes distinct card types
  Given staged creditcard source
  When I run "just build"
  Then dim_credit_card has one row per credit card
  And credit_card_key is unique and not null
  And card_type is not null and within the known set of card types
```
- [ ] `stg_adventure_works__creditcard` (view)
- [ ] `credit_card_key` surrogate; `accepted_values` on card_type
- [ ] `_models.yml`: PK unique+not_null, descriptions

### Inner loop (TDD)
`skipped — declarative SQL transform; dbt schema tests are the acceptance gate`

### Blocked by
None - can start immediately

---

## P2-06 — dim_sales_reason

### What to build
Staging view for `salesreason`; a `dim_sales_reason` with `sales_reason_key`, reason name, reason type.
(The order↔reason bridge is Phase 3; this is the dimension only, ADR-0003.)

### Acceptance criteria
```gherkin
Scenario: dim_sales_reason exposes reasons including Promotion
  Given staged salesreason source
  When I run "just build"
  Then dim_sales_reason has one row per sales reason
  And sales_reason_key is unique and not null
  And the "Promotion" reason is present
```
- [ ] `stg_adventure_works__salesreason` (view)
- [ ] `sales_reason_key` surrogate; not_null name/type
- [ ] `_models.yml`: PK unique+not_null, descriptions

### Inner loop (TDD)
`skipped — declarative SQL transform; dbt schema tests are the acceptance gate`

### Blocked by
None - can start immediately

---

## P2-07 — dim_order_status

### What to build
A `dim_order_status` mapping AdventureWorks order `status` codes (1–6) to human-readable labels
(e.g. 1=In process, 5=Shipped), with `order_status_key`. Built from a small seed or an inline mapping;
values validated against the codes present in staged `salesorderheader`.

### Acceptance criteria
```gherkin
Scenario: dim_order_status maps status codes to labels
  Given the set of order status codes used by AdventureWorks
  When I run "just build"
  Then dim_order_status has one row per status code with a non-null label
  And order_status_key is unique and not null
  And every status present in salesorderheader has a matching row in dim_order_status
```
- [ ] status→label mapping (seed `order_status.csv` or inline)
- [ ] `order_status_key` surrogate
- [ ] `_models.yml`: PK unique+not_null, relationship from staged header status, descriptions

### Inner loop (TDD)
`skipped — small declarative mapping; dbt schema/relationship tests are the acceptance gate`

### Blocked by
None - can start immediately
