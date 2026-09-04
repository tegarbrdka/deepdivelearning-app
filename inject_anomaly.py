import sqlite3
import json
from datetime import datetime

def inject_anomaly():
    db_path = r"f:\educlasify\educlassify.db"
    
    # We want to create an anomaly where the overall score is exactly 50%
    # But one aspect is very strong (e.g., Mindful 95%) and another is very weak (Digital 5%)
    # This triggers "Anomali 3 — Grade 2/3 dengan aspek sangat kuat" or general imbalance
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    scores = {
        "mindful": 95.0,
        "meaningful": 45.0,
        "joyful": 50.0,
        "pedagogis": 55.0,
        "digital": 5.0
    }
    
    sub_scores = {
        "mindful": {"aktivasi_fokus": 95.0, "metakognisi": 95.0, "kesadaran_fisik": 95.0},
        "meaningful": {"linking": 45.0, "realworld": 45.0, "asesmen": 45.0},
        "joyful": {"flow": 50.0, "kolaborasi": 50.0},
        "pedagogis": {},
        "digital": {}
    }
    
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            INSERT INTO predictions 
            (file_name, file_type, label, confidence, dli_score, dli_category, mindful_score, meaningful_score, joyful_score, pedagogis_score, digital_score, dli_data, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "RPP_Simulasi_Anomali_50_Persen.pdf",
            "document",
            "Deep Learning",
            88.5,
            50.0,
            "Perlu Perbaikan",
            95.0,  # mindful
            45.0,  # meaningful
            50.0,  # joyful
            55.0,  # pedagogis
            5.0,   # digital (Sangat lemah, memicu anomali)
            json.dumps({"scores": scores, "sub_scores": sub_scores}),
            now,
            1
        ))
        
        conn.commit()
        print("Berhasil menyuntikkan data anomali dengan skor 50%.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inject_anomaly()
