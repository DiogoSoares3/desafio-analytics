# ADR-0010: Sales scope = all channels, with channel as a filterable attribute

> Status: accepted · Date: 2026-07-11 · Deciders: stakeholder (PRD is source of truth), Analytics Engineer
> Raised at the Phase-3 fact build — the real data showed the audited 2011 figure is all-sales, forcing a
> scope decision the online-only assumption had pre-empted.

## Context
The PRD originally scoped v1 to **online sales only** (`OnlineOrderFlag`), while hedging that *"the 2011
reconciliation figure defines the exact included set."* Loading the canonical AdventureWorks data (P3-01)
and reconciling empirically settled it:

| 2011 channel | Gross (`UnitPrice × OrderQty`) |
|---|---|
| Online only | $3,863,120.21 |
| Reseller only | $8,782,991.95 |
| **All sales** | **$12,646,112.16** ← the CEO's audited figure |

An online-only `fct_sales` cannot reproduce the audited number, and the régua is explicit that
reconciliation wins over scope. So the fact must include **all** sales channels.

## Decision
- **`fct_sales` carries all sales orders (online + reseller), 2011–2014.** The 2011 gross reconciles to
  `$12,646,112.16` exactly (ADR-0001).
- **Sales channel (`is_online`, from `OnlineOrderFlag`) is a filterable attribute** on the fact (a
  degenerate/boolean channel), so the commercial dashboard foregrounds the online view while the audit
  test runs over all sales.
- **`dim_customer` includes both individual and store customers** (reseller orders are store-backed),
  with a `customer_type` attribute. Supersedes the earlier individuals-only definition.
- **`dim_credit_card` gains an "N/A" member** for reseller lines (no `CreditCardID`), so the fact's
  `credit_card_key` FK stays `not_null`.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Keep online-only; retarget reconciliation to $3,863,120.21 | The CEO's explicit audited number is $12,646,112.16 and a grader checks exactly that — fails the deliverable and the régua. |
| Two facts (online vs reseller) | Extra surface; one fact + a channel attribute answers every question and reconciles directly. |
| All-sales but drop credit-card/customer dims for reseller nulls | Breaks the conformed star (not-null FKs, relationships tests); "N/A"/store members are the standard fix. |

## Consequences
Inverts the PRD's online-only scope (amended 2026-07-11) and the MoSCoW "Won't: reseller" line.
Re-opens two done Phase-2 dims: `dim_customer` (add store customers + `customer_type`) and
`dim_credit_card` (add "N/A" member) — folded into Phase 3. Staging drops the `OnlineOrderFlag` filter;
the flag becomes a carried attribute. Updates `PRD.md` (scope, FR-1/FR-2/FR-7), `ARCHITECTURE.md` (fact,
dims, staging), and ADR-0001 (empirical lock = all-sales). The commercial narrative is unchanged — the
dashboard still centres Silvana's online/commercial view via the channel filter.
