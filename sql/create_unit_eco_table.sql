
CREATE OR REPLACE TABLE unit_eco_vw AS
WITH user_ltv_raw AS (
    SELECT u.channel,
        CASE WHEN u.reg_date::DATE < '2024-03-01' THEN 'early' ELSE 'late' END AS period,
        p.price * (COALESCE(s.end_date::DATE, '2024-07-01'::DATE) - s.start_date::DATE) / 30.0 AS ltv
    FROM users u
    JOIN subscriptions s ON u.user_id = s.user_id
    JOIN plans p ON s.plan_id = p.plan_id
),
ltv_agg AS (
    SELECT channel, period, ROUND(AVG(ltv), 2) AS avg_ltv
    FROM user_ltv_raw
    GROUP BY channel, period
),
cac_calc AS (
    SELECT ms.channel,
        CASE WHEN ms.month < '2024-03' THEN 'early' ELSE 'late' END AS period,
        ROUND(SUM(ms.spend) * 1.0 / NULLIF(COUNT(DISTINCT u.user_id), 0), 2) AS cac
    FROM marketing_spend ms
    LEFT JOIN users u ON ms.channel = u.channel AND strftime('%Y-%m', u.reg_date::DATE) = ms.month
    GROUP BY ms.channel, period
)
SELECT 
    l.channel, l.period, l.avg_ltv, c.cac,
    ROUND(l.avg_ltv / NULLIF(c.cac, 0), 2) AS ltv_cac_ratio,
    CASE 
        WHEN l.avg_ltv / NULLIF(c.cac, 0) >= 3 THEN 'Healthy'
        WHEN l.avg_ltv / NULLIF(c.cac, 0) >= 1 THEN 'At Risk'
        ELSE 'Unprofitable' 
    END AS status
FROM ltv_agg l
LEFT JOIN cac_calc c ON l.channel = c.channel AND l.period = c.period;