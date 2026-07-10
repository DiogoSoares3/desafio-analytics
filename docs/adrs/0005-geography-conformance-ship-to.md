# ADR-0005: Geography conformance — one dim_geography, fact resolves to ship-to

> Status: accepted · Date: 2026-07-10 · Deciders: engineer (via /grill-me)
> Raised during ARCHITECTURE authoring — PRD open question #4: bill-to vs ship-to for the sale's geography.

## Context
An online order links to multiple addresses (bill-to, ship-to) via `SalesOrderHeader → Address →
StateProvince → CountryRegion`. Questions c/d (top cities/states/countries by revenue) need exactly **one**
geography per sale, but bill-to and ship-to can differ.

## Decision
Build one conformed **`dim_geography`** at grain city + state/province + country (deduped across all
addresses). `fct_sales` resolves its geography FK to the **ship-to address** (`ShipToAddressID`) — where
the product went, the natural market lens for commercial analysis, and always present on an order.
`dim_customer` additionally carries a home-geography attribute (conformed to the same `dim_geography`),
but the fact's geographic slice is ship-to.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Slice by customer home address | Not tied to the actual transaction location; weaker "market" semantics. |
| Carry both bill-to and ship-to FKs on the fact | Ambiguous default slice for questions c/d; doubles geography joins for little v1 value. |

## Consequences
Single unambiguous geography per sale for questions c/d. Bill-to analysis is deferred (available in raw if
needed later). `dim_geography` is conformed and reused by `dim_customer`. Updates `ARCHITECTURE.md`
(components: `dim_geography`; fact FK = ship-to).
