-- Создание материализованной витрины данных для дашборда
-- DuckDB не поддерживает WITH в CREATE VIEW, поэтому используем TABLE
-- Это также улучшает производительность BI-инструментов

CREATE OR REPLACE TABLE dashboard_vw AS
WITH mrr_dynamics AS (
    SELECT strftime('%Y-%m', start_date::DATE) AS month, SUM(p.price) AS flow_mrr
    FROM subscriptions s JOIN plans p ON s.plan_id = p.plan_id GROUP BY month
    UNION ALL
    SELECT strftime('%Y-%m', end_date::DATE) AS month, SUM(p.price) * -1 AS flow_mrr
    FROM subscriptions s JOIN plans p ON s.plan_id = p.plan_id WHERE end_date IS NOT NULL GROUP BY month
),
mrr_agg AS (
    SELECT month, SUM(flow_mrr) AS net_change FROM mrr_dynamics GROUP BY month
),
mrr_cumulative AS (
    SELECT month, ROUND(SUM(net_change) OVER (ORDER BY month), 2) AS mrr FROM mrr_agg
),
mrr_with_prev AS (
    SELECT month, mrr, LAG(mrr) OVER (ORDER BY month) AS prev_mrr FROM mrr_cumulative
),
dynamics AS (
    SELECT 
        month, mrr,
        CASE WHEN prev_mrr > 0 THEN ROUND((mrr - prev_mrr) / prev_mrr * 100, 1) END AS growth_rate_pct
    FROM mrr_with_prev
    WHERE month BETWEEN '2024-01' AND '2024-06'
),
decomposition AS (
    SELECT 
        month,
        SUM(CASE WHEN type = 'new' THEN val ELSE 0 END) AS new_mrr,
        SUM(CASE WHEN type = 'churn' THEN val ELSE 0 END) AS churned_mrr
    FROM (
        SELECT strftime('%Y-%m', start_date::DATE) AS month, 'new' AS type, SUM(p.price) AS val
        FROM subscriptions s JOIN plans p ON s.plan_id = p.plan_id GROUP BY month
        UNION ALL
        SELECT strftime('%Y-%m', end_date::DATE) AS month, 'churn' AS type, SUM(p.price) * -1 AS val
        FROM subscriptions s JOIN plans p ON s.plan_id = p.plan_id WHERE end_date IS NOT NULL GROUP BY month
    ) t
    WHERE month BETWEEN '2024-01' AND '2024-06'
    GROUP BY month
),
retention_raw AS (
    SELECT cu.channel, cu.cohort, cu.user_id, COUNT(DISTINCT e.event_time) > 0 AS is_active_m2
    FROM (
        SELECT user_id, channel, reg_date::DATE AS reg_date,
            CASE WHEN reg_date::DATE < '2024-04-01' THEN 'Jan-Mar' ELSE 'Apr+' END AS cohort
        FROM users
    ) cu
    LEFT JOIN events e ON cu.user_id = e.user_id
        AND e.event_time::TIMESTAMP >= cu.reg_date + INTERVAL '60 days'
        AND e.event_time::TIMESTAMP < cu.reg_date + INTERVAL '90 days'
    GROUP BY cu.channel, cu.cohort, cu.user_id
),
retention AS (
    SELECT channel, cohort, ROUND(AVG(is_active_m2::INT) * 100, 1) AS retention_m2_pct
    FROM retention_raw GROUP BY channel, cohort
),
user_ltv_raw AS (
    SELECT u.channel,
        CASE WHEN u.reg_date::DATE < '2024-03-01' THEN 'early' ELSE 'late' END AS period,
        p.price * (COALESCE(s.end_date::DATE, '2024-07-01'::DATE) - s.start_date::DATE) / 30.0 AS ltv
    FROM users u JOIN subscriptions s ON u.user_id = s.user_id JOIN plans p ON s.plan_id = p.plan_id
),
ltv_agg AS (
    SELECT channel, period, ROUND(AVG(ltv), 2) AS avg_ltv
    FROM user_ltv_raw GROUP BY channel, period
),
cac_calc AS (
    SELECT ms.channel,
        CASE WHEN ms.month < '2024-03' THEN 'early' ELSE 'late' END AS period,
        ROUND(SUM(ms.spend) * 1.0 / NULLIF(COUNT(DISTINCT u.user_id), 0), 2) AS cac
    FROM marketing_spend ms
    LEFT JOIN users u ON ms.channel = u.channel AND strftime('%Y-%m', u.reg_date::DATE) = ms.month
    GROUP BY ms.channel, period
),
unit_eco AS (
    SELECT l.channel, l.period, l.avg_ltv, c.cac,
        ROUND(l.avg_ltv / NULLIF(c.cac, 0), 2) AS ltv_cac_ratio,
        CASE 
            WHEN l.avg_ltv / NULLIF(c.cac, 0) >= 3 THEN 'Healthy'
            WHEN l.avg_ltv / NULLIF(c.cac, 0) >= 1 THEN 'At Risk'
            ELSE 'Unprofitable' 
        END AS status
    FROM ltv_agg l LEFT JOIN cac_calc c ON l.channel = c.channel AND l.period = c.period
)
SELECT 
    d.month, d.mrr, d.growth_rate_pct,
    dc.new_mrr, dc.churned_mrr,
    r.channel, r.cohort, r.retention_m2_pct,
    ue.period, ue.avg_ltv, ue.cac, ue.ltv_cac_ratio, ue.status
FROM dynamics d
JOIN decomposition dc ON d.month = dc.month
CROSS JOIN retention r
CROSS JOIN unit_eco ue;