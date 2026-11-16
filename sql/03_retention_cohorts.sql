WITH cohort_users AS (
    SELECT u.user_id, u.channel, u.reg_date::DATE AS reg_date,
        CASE 
            WHEN u.reg_date::DATE < '2024-04-01' THEN 'Jan-Mar' 
            ELSE 'Apr+'
        END AS cohort
    FROM users u
),
activity_check AS (
    SELECT cu.user_id, cu.channel, cu.cohort,
            COUNT(DISTINCT e.event_time) > 0 AS is_active_m2
    FROM cohort_users cu
    LEFT JOIN events e
        ON cu.user_id = e.user_id
        AND e.event_time::TIMESTAMP >= cu.reg_date + INTERVAL '60 days'
        AND e.event_time::TIMESTAMP < cu.reg_date + INTERVAL '90 days'
    GROUP BY cu.user_id, cu.channel, cu.cohort
)

SELECT channel, cohort,
        ROUND(AVG(is_active_m2::INT) * 100, 1) AS retention_m2_pct,
        COUNT(*) AS users_in_cohort
FROM activity_check
GROUP BY channel, cohort
ORDER BY channel, cohort;