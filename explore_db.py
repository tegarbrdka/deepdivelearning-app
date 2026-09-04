import pandas as pd
import sqlite3

def explore_db(db_path):
    print(f"\n--- Exploring {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)['name'].tolist()
        
        for t in tables:
            try:
                count = pd.read_sql_query(f"SELECT COUNT(*) as c FROM {t}", conn).iloc[0]['c']
                if count > 0:
                    print(f"Table '{t}' has {count} rows.")
                    df = pd.read_sql_query(f"SELECT * FROM {t} LIMIT 1", conn)
                    print(f"Columns: {list(df.columns)}")
            except Exception as e:
                pass
        conn.close()
    except Exception as e:
        print("Error:", e)

def main():
    explore_db("f:/educlasify/educlasify.db")
    explore_db("f:/educlasify/educlassify.db")

if __name__ == "__main__":
    main()
