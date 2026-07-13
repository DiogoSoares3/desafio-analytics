# Commercial Recommendations — Adventure Works

**Prepared for:** Silvana Teixeira, Commercial Director.

Silvana, you told us you'd rather put next quarter's budget into promotional activity than into more
data infrastructure, and that you've been burned before by "data-driven" tools that never paid off.
Fair — so this document does not ask you to trust a slide. Every recommendation below cites a number
that comes straight out of the **Adventure Works — Sales** dashboard or the exploratory data analysis
behind it, and every one of those numbers reconciles to the audited 2011 gross-sales figure
($12,646,112.16) that the finance team already signed off on. You can open the dashboard, apply the
same filters, and get the same numbers — that is the whole point of building it this way. The
recommendations are ordered by expected commercial impact, highest first. (If you want to check the
sourcing yourself, § "How to verify these numbers" at the end points to exactly where each figure comes
from.)

## Prioritized recommendations

### 1. Protect and re-invest in the reseller channel — it is 73.4% of revenue from 12.1% of orders

Resellers place only 12.1% of all orders (3,806 of 31,465) but generate **73.4%** of total gross
revenue ($81.0M of $110,373,889.31), because their average order value is **$21,286.18** against
**$1,061.45** for online — a **~20x** gap (see the dashboard's hero KPIs and the channel-mix view in the
EDA). Any plan to shift spend
toward "more promotions to end consumers" without first protecting reseller account health is optimizing
the 26.6% of revenue, not the 73.4%. Action: build a reseller account-health scorecard (order frequency,
AOV trend) as a filtered view of the existing dashboard (Sales Channel = Reseller), reviewed monthly with
key accounts before any consumer-promotion budget is approved.

### 2. Concentrate the catalog investment on Bikes — 86.2% of revenue from 32.8% of units

Bikes account for **86.2%** of gross revenue ($95.1M) while representing only **32.8%** of units sold
(90,268 of 274,914) — the highest revenue-per-unit category by a wide margin (see "Question a: Orders /
Quantity / Value by Product" on the dashboard, sliceable by product/category, and the product-mix chart
in the EDA). Components,
Clothing, and Accessories together move 67.2% of units for 13.8% of revenue. Action: prioritize Bikes
in merchandising and inventory planning, and treat the other three categories as basket-builders (bundle
promotions), not as standalone revenue drivers — a mix decision the data supports, not a hunch.

### 3. Make the top 10 customers and top 5 cities named accounts, not anonymous rows in a report

The single largest customer, **Brakes and Gears**, alone drove **$882,276.4966** in gross revenue (see
"Question c: Top 10 Customers"); the top city, **Toronto**, drove **$4,498,883.7327** (see
"Question d: Top 5 Cities"), roughly 27% more than the second-ranked city, London ($2,754,814). Action:
assign a named commercial owner to each of the top 10 customers and top 5 cities
and track their revenue trend on the dashboard's Question e time-series chart month over month — the
90/10 rule is visible in the data, so treat those accounts as the retention priority they already are.

### 4. Geography: defend the US base (57.4% of revenue) while formalizing a Canada growth play

The United States alone accounts for **57.4%** of gross revenue ($63.3M of $110,373,889.31); Canada is
a distant but clear second at **$16,441,130** (see the geography views on the dashboard and in the EDA,
both filterable by country/state/city). Action:
do not spread commercial effort evenly across all 6 countries in the model — protect the US base first,
then run a Canada-specific push (it is already ~15% of revenue on its own, ahead of Australia, the UK,
France, and Germany combined at the country level).

### 5. Reframe the promotion debate: "On Promotion" orders are real ($6,361,828.95), but the discount is not where you think it is

This is the direct answer to your skepticism, Silvana. The Promotion-Impact tile on the dashboard
(reconciling the EDA's independent figure exactly) shows **3,515** online orders tagged "On Promotion"
drove **$6,361,828.95** in gross revenue — about **5.8%** of total revenue, a real and material number,
so "spend on promotions" is not wrong on its face. But the model also shows the actual dollar discount
amount — **$527,507.91** total — sits **entirely on the reseller/store channel** (60,919 order lines) and
is **structurally zero** on every one of the 60,398 online order lines, including all 3,515
"On Promotion" ones (see the EDA's promotion/discount-impact section). In other words, the online
"Promotion" tag in this data is a *reason code* (why the customer says they bought), not a price cut —
the top product under that reason, **Water Bottle - 30 oz.** (546 units, see "Question f: Top Product —
On Promotion" on the dashboard), sold at full margin. The actual price discounting happens on reseller
deals, a completely different
lever than a marketing promotion. Action: before committing next quarter's budget to online promotions,
separate the two questions the data now lets you ask separately — "does a promotion *reason code* change
what customers buy" (yes, modestly, ~5.8% of revenue) versus "does discounting *price* move volume"
(a reseller-channel question, $527,507.91 in discounts against $81.0M in reseller revenue, ~0.65% of
reseller revenue). They are not the same lever, and conflating them is exactly the kind of hunch this
model exists to replace with a number you can re-run yourself.

### 6. Make the dashboard the monthly commercial review artifact, not a one-off report

Every number in this document is reproducible by anyone on your team, end to end, offline — the same
$110,373,889.31 total revenue, 31,465 orders, and $3,491.07 average order value the CEO's audit
reconciles to $12,646,112.16 for 2011 alone. That reproducibility is the answer to "I've been burned by
data-driven promises before": this is not a one-time PowerPoint, it is a rebuildable model with 138
automated tests attached. Action: adopt the "Adventure Works — Sales" dashboard
as the standing monthly commercial review artifact — filtered live by product, channel, geography,
customer, and sales reason — replacing ad-hoc spreadsheet pulls, and revisit this recommendations list
each quarter against the same live figures.

## How to verify these numbers yourself

1. `just build` (rebuilds `data/adventureworks.duckdb` from the committed source Parquet, all 138
   dbt tests green).
2. Open `bi/dashboards/adventure_works_sales.yaml`'s charts (see `bi/README.md` for local Superset
   import instructions) or run `uv run python scripts/test_recommendations.py`, which independently
   recomputes every figure cited above directly from the built marts.
3. Run `notebooks/eda.ipynb` end-to-end (`just eda`) for the independent EDA cross-check of the same
   product-mix, channel, geography, and promotion figures.
