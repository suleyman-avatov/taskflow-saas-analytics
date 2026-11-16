
WITH monthly_flow AS (
    SELECT  strftime('%Y-%m', start_date::DATE) AS month, SUM(p.price) AS flow_mrr
    FROM subscriptions s
    JOIN plans p ON s.plan_id = p.plan_id
    GROUP BY month
    
    UNION ALL
    
    SELECT strftime('%Y-%m', end_date::DATE) AS month, SUM(p.price) * -1 AS flow_mrr
    FROM subscriptions s
    JOIN plans p ON s.plan_id = p.plan_id
    WHERE end_date IS NOT NULL
    GROUP BY month
), 
monthly_net AS (
    SELECT month, SUM(flow_mrr) AS net_change
    FROM monthly_flow
    GROUP BY month
),
mrr_cumulative AS (
    SELECT month, ROUND(SUM(net_change) OVER (ORDER BY month), 2) AS mrr
    FROM monthly_net
),
mrr_with_prev AS (
    SELECT month, mrr, LAG(mrr) OVER (ORDER BY month) AS prev_mrr
    FROM mrr_cumulative
)
SELECT month, mrr,
    CASE 
        WHEN prev_mrr IS NOT NULL AND prev_mrr > 0
        THEN ROUND((mrr - prev_mrr) / prev_mrr * 100, 1)
        ELSE NULL
    END AS growth_rate_pct
FROM mrr_with_prev
WHERE month BETWEEN '2024-01' AND '2024-06'
ORDER BY month;