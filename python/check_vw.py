import duckdb

DB_PATH = "data/taskflow_real.db"
conn = duckdb.connect(DB_PATH)

print("=" * 70)
print("ПРОВЕРКА 1: Значения в витрине dashboard_vw")
print("=" * 70)
result = conn.execute("""
    SELECT DISTINCT channel, period, avg_ltv, cac, ltv_cac_ratio 
    FROM dashboard_vw 
    ORDER BY channel, period
""").fetchdf()
print(result.to_string(index=False))

print("\n" + "=" * 70)
print("ПРОВЕРКА 2: Прямой расчёт LTV из исходных таблиц")
print("=" * 70)
result2 = conn.execute("""
    SELECT 
        u.channel,
        CASE WHEN u.reg_date::DATE < '2024-03-01' THEN 'early' ELSE 'late' END AS period,
        ROUND(AVG(p.price * (COALESCE(s.end_date::DATE, '2024-07-01'::DATE) - s.start_date::DATE) / 30.0), 2) AS avg_ltv
    FROM users u
    JOIN subscriptions s ON u.user_id = s.user_id
    JOIN plans p ON s.plan_id = p.plan_id
    GROUP BY u.channel, period
    ORDER BY u.channel, period
""").fetchdf()
print(result2.to_string(index=False))

print("\n" + "=" * 70)
print("ПРОВЕРКА 3: Прямой расчёт CAC из исходных таблиц")
print("=" * 70)
result3 = conn.execute("""
    SELECT 
        ms.channel,
        CASE WHEN ms.month < '2024-03' THEN 'early' ELSE 'late' END AS period,
        ROUND(SUM(ms.spend) * 1.0 / NULLIF(COUNT(DISTINCT u.user_id), 0), 2) AS cac
    FROM marketing_spend ms
    LEFT JOIN users u ON ms.channel = u.channel AND strftime('%Y-%m', u.reg_date::DATE) = ms.month
    GROUP BY ms.channel, period
    ORDER BY ms.channel, period
""").fetchdf()
print(result3.to_string(index=False))

conn.close()