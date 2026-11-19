import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = "data/taskflow_real.db"
OUTPUT_PATH = Path("data/dashboard_vw.xlsx")


def export_to_excel():
    conn = duckdb.connect(DB_PATH)

    df_main = conn.execute(
        "SELECT * FROM dashboard_vw ORDER BY month, channel, cohort, period"
    ).fetchdf()
    df_main = df_main.convert_dtypes(
        convert_string=True, convert_integer=False, convert_floating=False
    )

    df_ue = conn.execute(
        "SELECT * FROM unit_eco_vw ORDER BY channel, period"
    ).fetchdf()
    df_ue = df_ue.convert_dtypes(
        convert_string=True, convert_integer=False, convert_floating=False
    )

    conn.close()

    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, index=False, sheet_name="Dashboard_VW")
        df_ue.to_excel(writer, index=False, sheet_name="Unit_Economics")

        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            df = df_main if sheet_name == "Dashboard_VW" else df_ue
            for i, col in enumerate(df.columns):
                try:
                    max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                    ws.column_dimensions[chr(65 + i)].width = min(max_len, 40)
                except Exception:
                    ws.column_dimensions[chr(65 + i)].width = 15

    print(f" Экспортировано:")
    print(f"   Dashboard_VW:    {len(df_main)} строк")
    print(f"   Unit_Economics:  {len(df_ue)} строк")
    print(f"   → {OUTPUT_PATH}")


if __name__ == "__main__":
    export_to_excel()