SELECT month, SUM(new_mrr) AS new_mrr,
        SUM(churned_mrr) AS churned_mrr,
        SUM(new_mrr + churned_mrr) AS net_changle
FROM (
    SELECT strftime('%Y-%m', start_date::DATE) AS month, 
        SUM(p.price) AS new_mrr,
        0 AS churned_mrr
    FROM subscriptions s
    JOIN plans p ON s.plan_id = p.plan_id
    GROUP BY month

    UNION ALL

    SELECT strftime('%Y-%m', end_date::DATE) AS month,
            0 AS new_mrr,
            SUM(p.price) * -1 AS churned_mrr
    FROM subscriptions s
    JOIN plans p ON s.plan_id = p.plan_id
    WHERE end_date IS NOT NULL
    GROUP BY month 
) AS mrr_components
WHERE month BETWEEN '2024-01' AND '2024-06'
GROUP BY month
ORDER BY month;
