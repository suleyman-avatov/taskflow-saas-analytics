

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = "data/taskflow_real.db"
OUTPUT_PATH = Path("data/dashboard_vw.xlsx")


def export_dashboard_to_excel():
    conn = duckdb.connect(DB_PATH)
    
    tables = conn.execute("SHOW TABLES").fetchdf()['name'].tolist()
    if 'dashboard_vw' not in tables:
        print("Таблица dashboard_vw не найдена. Сначала выполните sql/create_dashboard_vw.sql")
        return
    
    df = conn.execute("SELECT * FROM dashboard_vw ORDER BY month, channel, cohort, period").fetchdf()
    df = df.convert_dtypes(convert_string=True, convert_integer=False, convert_floating=False)
    conn.close()
    
    if df.empty:
        print(" Витрина пуста")
        return
    
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    
    with pd.ExcelWriter(OUTPUT_PATH, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dashboard_VW')
        
        worksheet = writer.sheets['Dashboard_VW']
        for i, col in enumerate(df.columns):
            try:
                lengths = df[col].astype(str).str.len()
                max_len = max(lengths.max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + i)].width = min(max_len, 40)
            except Exception:
                worksheet.column_dimensions[chr(65 + i)].width = 15
    
    print(f"Экспортировано {len(df)} строк → {OUTPUT_PATH}")
    print(f" Колонки: {', '.join(df.columns)}")
    print(f"Период: {df['month'].min()} – {df['month'].max()}")


if __name__ == "__main__":
    export_dashboard_to_excel()