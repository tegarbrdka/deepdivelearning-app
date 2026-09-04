import pandas as pd
import sqlite3

def main():
    db_path = "f:/educlasify/educlassify.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Ekstrak data hasil analisis video
        query = """
        SELECT 
            job_id as ID_Video,
            mindful_score as Skor_Mindful,
            meaningful_score as Skor_Meaningful,
            joyful_score as Skor_Joyful,
            overall_3m_score as Skor_Overall_Deep_Learning,
            gaze_score as Gaze_Score,
            posture_score as Posture_Score,
            teacher_talk_pct as Persentase_Teacher_Talk,
            student_talk_pct as Persentase_Student_Talk,
            expression_score as Expression_Score,
            collaboration_score as Collaboration_Score,
            created_at as Waktu_Analisis
        FROM video_analysis_results
        ORDER BY created_at ASC
        """
        
        df = pd.read_sql_query(query, conn)
        
        # Simpan ke Excel
        output_file = "f:/educlasify/Data_Asli_Output_Sistem_3M.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Berhasil mengekstrak {len(df)} baris data ASLI dari sistem ke {output_file}")
        
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
