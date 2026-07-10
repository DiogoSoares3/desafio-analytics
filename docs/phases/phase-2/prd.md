# Phase 2 — Dimensions (seven conformed dims · staging → mart · PK + data-quality tests)

> **Derived, internal — no separate human sign-off** (root `PRD.md` + `ARCHITECTURE.md` are the only
> human-validated baselines). Thin projection: references baselines by requirement ID / seam, does not
> restate them.

## Realizes (requirement IDs)
`FR-1` (seven conformed dimensions), the **dimension slice of `FR-4`** (PK `unique`+`not_null` +
data-quality tests on every dim), `FR-5` (mart documentation). Continues `NFR-1/2/3/4`.

## Capabilities in scope
Root MoSCoW: *"Conformed dimensional model (7 dims + sales fact)"* — the **7 dims** portion; *"Source/PK/
data-quality tests all green"* — dim PK + data-quality tests; *"Model + column documentation"* — dims.

## Seam(s) touched
**Model schema / PK tests** (`_models.yml` on each `dim_*`) — `ARCHITECTURE.md` → *Seams* #2. Builds the
**Silver** staging layer (`stg_adventure_works__*`, views) feeding **Gold** `dim_*` (tables). Keys per
[ADR-0007](../../adrs/0007-surrogate-keys.md); SCD Type 1 [ADR-0008](../../adrs/0008-scd-type-1.md);
geography [ADR-0005](../../adrs/0005-geography-conformance-ship-to.md); date-spine
[ADR-0006](../../adrs/0006-date-spine.md).

## Depends on
Phase 1 (Foundation) — done. Each dim slice builds its own staging models vertically (source → staging →
dim → tests); shared lookups are built by the first slice that needs them.

## DoD gate (this phase)
- All seven `dim_*` build green (`just build`); each is a `table` in the Gold layer.
- Each dim has a hashed surrogate PK `<entity>_key` (`dbt_utils.generate_surrogate_key`) with
  `unique` + `not_null` tests passing.
- Data-quality tests pass: `not_null` on required attributes, `accepted_values` on domains where they
  exist, `relationships` where a dim references another (conformed geography).
- Every dim model and column is documented (`description:`), grader-readable.
- `just test` green (all model tests); `just lint` green (sqlfluff on new SQL).

## Deferred to later phases
- `fct_sales`, `bridge_order_sales_reason`, and reconciliation tests → Phase 3.
- EDA notebook, KPIs, Superset dashboard → Phase 4 + manual/external.
- Customer home-geography enrichment is **optional** here (fact geography = ship-to, ADR-0005); include
  only if the seed data supports it cleanly, else defer.
