
import sys
import duckdb
from pathlib import Path


def run_sql_file(file_path: str):
    path = Path(file_path)
    
    if not path.exists():
        print(f"Файл не найден: {path}")
        sys.exit(1)

    db_path = "data/taskflow_real.db"
    con = duckdb.connect(db_path)
    
    try:
        sql_content = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(" Ошибка кодировки файла. Убедитесь, что файл сохранен в UTF-8")
        sys.exit(1)

    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    print(f" Выполняю {len(statements)} инструкций из {path.name}...\n")
    
    for i, stmt in enumerate(statements, 1):
        print(f"--- Инструкция {i} ---")
        try:
            result = con.execute(stmt)
            
            if result.description:
                df = result.fetchdf()
                if df.empty:
                    print("(пустой результат)")
                else:
                    print(df.to_string(index=False))
            else:
                affected = result.rowcount
                print(f" Выполнено успешно (затронуто строк: {affected})")
                
        except Exception as e:
            print(f" Ошибка в инструкции {i}: {e}")
            break
    
    con.close()
    print("\n Готово!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python run_sql.py <путь_к_файлу.sql>")
        print("Пример: python run_sql.py sql/01_mrr_dynamics.sql")
        sys.exit(1)
        
    run_sql_file(sys.argv[1])