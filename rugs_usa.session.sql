SELECT * FROM (
    SELECT *, 
    ROW_NUMBER() OVER (PARTITION BY ORDER_ID
        ORDER BY event_time DESC) AS row_num
    FROM order_events
    )
WHERE row_num = 1;

SELECT 
    customer_key
    , ORDER_ID
    , net_revenue
    , SUM(net_revenue) OVER (PARTITION BY customer_key ORDER BY date_key
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_ltv
    , net_revenue - LAG(net_revenue) OVER (PARTITION BY customer_key ORDER BY date_key) AS delta_vs_prev
    , RANK() OVER (PARTITION BY customer_key ORDER BY net_revenue DESC) AS rev_rank
FROM fct_order_lines
ORDER BY customer_key, date_key
LIMIT 100;