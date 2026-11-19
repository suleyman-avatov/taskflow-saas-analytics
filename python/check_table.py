import duckdb

conn = duckdb.connect("data/taskflow_real.db")

print(" Все таблицы в базе:")
tables = conn.execute("SHOW TABLES").fetchdf()
print(tables.to_string(index=False))

print("\n Содержимое unit_eco_vw:")
try:
    result = conn.execute("SELECT * FROM unit_eco_vw ORDER BY channel, period").fetchdf()
    print(result.to_string(index=False))
except Exception as e:
    print(f"Ошибка чтения таблицы: {e}")

conn.close()