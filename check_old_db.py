import pandas as pd
from sqlalchemy import create_engine
import sqlite3

def main():
    # Coba baca dari database lama yang typo namanya (educlasify.db)
    db_path = "f:/educlasify/educlasify.db"
    
    try:
        conn = sqlite3.connect(db_path)
        # Cek apakah tabel ada
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
        print("Tabel di DB lama:", tables['name'].tolist())
        
        if 'groundtruthannotation' in [t.lower() for t in tables['name'].tolist()]:
            # Cari nama tabel aslinya
            table_name = [t for t in tables['name'].tolist() if t.lower() == 'groundtruthannotation'][0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            print(f"Berhasil menemukan {len(df)} baris data GroundTruth di DB lama!")
            
            if len(df) > 0:
                # Coba extract sesuai format
                final_df = df.copy()
                final_df.to_excel("f:/educlasify/Data_Asli_Observasi_3M.xlsx", index=False)
                print("Data ASLI berhasil diekstrak ke Data_Asli_Observasi_3M.xlsx")
        else:
            print("Tabel GroundTruthAnnotation tidak ditemukan di DB lama.")
            
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
