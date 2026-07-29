# RugsUSA practice problems — 10 SQL drills

Run against `rugsusa_practice.duckdb`. **Attempt each cold before scrolling to the answers.**

```
pip install duckdb
python q.py                     # interactive: type SQL, blank line runs it
python q.py "SELECT 1"          # one-off
python q.py -f myquery.sql      # from a file
```

## Schema

| Table | Rows | Notes |
|---|---|---|
| `fct_order_lines` | 32,902 | grain = one line item per order. FKs + measures + `status` |
| `dim_date` | 731 | 2024-01-01 → 2025-12-31, `date_key` = YYYYMMDD int |
| `dim_product` | 151 | **SCD Type 2** — `is_current`, `effective_date`, `expiration_date` |
| `dim_customer` | 860 | some have zero orders; `segment` has NULLs |
| `dim_channel` | 5 | Website / Amazon / Wayfair / Phone |
| `dim_promotion` | 8 | includes a "No Promotion" row |
| `order_events` | 9,719 | multiple rows per order + real duplicates |
| `web_events` | 5,208 | clickstream for sessionization |
| `stg_product` | 50 | incoming batch for MERGE/SCD2 practice |
| `raw_orders` | 500 | nested JSON payloads |

Deliberate quirks: 46 days with zero sales, 60 customers with no orders, 58 duplicate event rows, NULLs in `color` and `segment`, 31 products with two SCD2 versions.

---

## The problems

**P1 · Dedup.** Return exactly one row per `order_id` from `order_events` — its most recent status. *(expect 3,685 rows)*

**P2 · Windows.** For each customer's order lines: running lifetime revenue, change vs previous line, and rank of each line within the customer by revenue.

**P3 · Conditional aggregation.** Per collection: total lines, returned lines, and average revenue of completed lines only. *(6 rows)*

**P4 · Anti-join.** Customers who have never placed an order. *(60 rows)*

**P5 · Sessionization.** Assign `session_id` to `web_events` where a new session starts after 30 minutes of inactivity.

**P6 · Date spine.** Daily completed revenue for 2025 with zero-filled gaps. Then: which days had no sales at all? *(46 across both years)*

**P7 · SCD Type 2.** Find products with more than one version, show both rows. Then: current-only product list. *(31 products have 2 versions)*

**P8 · Top-N per group.** Top 3 products by revenue within each collection. *(18 rows)*

**P9 · MERGE prep.** Which `stg_product` rows are new vs existing? *(10 new)*

**P10 · Business metrics.** AOV, return rate, and monthly revenue by channel. *(AOV ≈ 1771.38, return rate ≈ 16.46%)*

---

## Answers

<details>

### P1
```sql
SELECT * FROM order_events
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY event_time DESC) = 1;
```

### P2
```sql
SELECT customer_key, order_id, net_revenue,
  SUM(net_revenue) OVER (PARTITION BY customer_key ORDER BY date_key
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)      AS running_ltv,
  net_revenue - LAG(net_revenue) OVER (PARTITION BY customer_key
        ORDER BY date_key)                                     AS delta_vs_prev,
  RANK() OVER (PARTITION BY customer_key ORDER BY net_revenue DESC) AS rev_rank
FROM fct_order_lines;
```

### P3
```sql
SELECT p.collection,
  COUNT(*)                                             AS total_lines,
  COUNT(*) FILTER (WHERE f.status = 'returned')        AS returned_lines,
  ROUND(AVG(f.net_revenue) FILTER (WHERE f.status = 'completed'), 2) AS avg_completed
FROM fct_order_lines f
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY 1 ORDER BY 2 DESC;
```

### P4
```sql
SELECT c.customer_key, c.customer_id
FROM dim_customer c
WHERE NOT EXISTS (SELECT 1 FROM fct_order_lines f WHERE f.customer_key = c.customer_key);
```

### P5
```sql
WITH flagged AS (
  SELECT customer_key, event_time, event_type,
    CASE WHEN DATE_DIFF('minute',
              LAG(event_time) OVER (PARTITION BY customer_key ORDER BY event_time),
              event_time) > 30
         OR LAG(event_time) OVER (PARTITION BY customer_key ORDER BY event_time) IS NULL
         THEN 1 ELSE 0 END AS is_new_session
  FROM web_events
)
SELECT customer_key, event_time, event_type,
  SUM(is_new_session) OVER (PARTITION BY customer_key ORDER BY event_time) AS session_id
FROM flagged ORDER BY customer_key, event_time;
```

### P6
```sql
SELECT d.full_date, COALESCE(SUM(f.net_revenue), 0) AS revenue
FROM dim_date d
LEFT JOIN fct_order_lines f
       ON f.date_key = d.date_key AND f.status = 'completed'
WHERE d.year = 2025
GROUP BY 1 ORDER BY 1;

-- days with no sales at all
SELECT d.full_date FROM dim_date d
WHERE NOT EXISTS (SELECT 1 FROM fct_order_lines f WHERE f.date_key = d.date_key)
ORDER BY 1;
```
Note the join condition placement: `status = 'completed'` belongs in the `ON` clause, not `WHERE` — in the `WHERE` it would filter out the very null rows the left join is there to preserve.

### P7
```sql
SELECT * FROM dim_product
WHERE product_id IN (SELECT product_id FROM dim_product GROUP BY 1 HAVING COUNT(*) > 1)
ORDER BY product_id, effective_date;

-- current view only
SELECT * FROM dim_product WHERE is_current;
```

### P8
```sql
SELECT collection, product_id, revenue FROM (
  SELECT p.collection, p.product_id, SUM(f.net_revenue) AS revenue,
         ROW_NUMBER() OVER (PARTITION BY p.collection ORDER BY SUM(f.net_revenue) DESC) AS rn
  FROM fct_order_lines f
  JOIN dim_product p ON p.product_key = f.product_key
  GROUP BY 1, 2
) WHERE rn <= 3 ORDER BY collection, revenue DESC;
```

### P9
```sql
SELECT s.product_id,
  CASE WHEN p.product_id IS NULL THEN 'new' ELSE 'existing' END AS load_action
FROM stg_product s
LEFT JOIN (SELECT DISTINCT product_id FROM dim_product) p
       ON p.product_id = s.product_id
ORDER BY 2, 1;
```

### P10
```sql
-- AOV (grain matters: divide by distinct orders, not line count)
SELECT ROUND(SUM(net_revenue) / COUNT(DISTINCT order_id), 2) AS aov
FROM fct_order_lines WHERE status = 'completed';

-- return rate
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'returned') / COUNT(*), 2) AS return_rate_pct
FROM fct_order_lines;

-- monthly revenue by channel
SELECT d.year, d.month, ch.channel_name, ROUND(SUM(f.net_revenue), 2) AS revenue
FROM fct_order_lines f
JOIN dim_date d    ON d.date_key = f.date_key
JOIN dim_channel ch ON ch.channel_key = f.channel_key
WHERE f.status = 'completed'
GROUP BY 1, 2, 3 ORDER BY 1, 2, 4 DESC;
```

</details>

---

## Two traps worth triggering on purpose

**Fan-out.** Run this and watch revenue inflate — a product joined at the wrong grain duplicates fact rows:
```sql
SELECT SUM(f.net_revenue) FROM fct_order_lines f
JOIN dim_product p ON p.product_id =
     (SELECT product_id FROM dim_product WHERE product_key = f.product_key);
```
Joining on `product_id` instead of `product_key` matches every SCD2 version, doubling rows for the 31 versioned products. This is exactly the bug you describe catching in interviews.

**NOT IN with NULLs.** `dim_customer.segment` has 231 NULLs:
```sql
SELECT COUNT(*) FROM dim_customer WHERE segment NOT IN (SELECT segment FROM dim_customer);
```
Returns 0 — not because no rows qualify, but because a single NULL makes every comparison UNKNOWN. Fix with `NOT EXISTS`.
