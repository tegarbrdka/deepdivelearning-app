import pandas as pd
import sqlite3

def main():
    db_path = "f:/educlasify/educlassify.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Ekstrak data hasil analisis dokumen (RPP) dari tabel predictions
        query = """
        SELECT 
            file_name as Nama_Dokumen_RPP,
            dli_category as Kategori_DLI,
            dli_score as Skor_DLI_Keseluruhan,
            mindful_score as Skor_Mindful,
            meaningful_score as Skor_Meaningful,
            joyful_score as Skor_Joyful,
            pedagogis_score as Skor_Pedagogis,
            digital_score as Skor_Digital,
            confidence as Confidence_AI,
            created_at as Waktu_Analisis
        FROM predictions
        WHERE file_type = 'document' OR file_name LIKE '%.pdf' OR file_name LIKE '%.doc%'
        ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        output_file = "f:/educlasify/Data_Asli_Output_Sistem_RPP.xlsx"
        
        if len(df) > 0:
            df.to_excel(output_file, index=False)
            print(f"Berhasil mengekstrak {len(df)} baris data ASLI analisis RPP ke {output_file}")
        else:
            print("Tidak ditemukan data analisis dokumen di tabel predictions.")
            # Coba cek semua data di predictions tanpa filter jika kosong
            df_all = pd.read_sql_query("SELECT * FROM predictions", conn)
            print(f"Total baris di predictions: {len(df_all)}")
            if len(df_all) > 0:
                print("Tipe file yang ada:", df_all['file_type'].unique())
        
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
