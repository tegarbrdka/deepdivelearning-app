import pandas as pd
import numpy as np
from backend.database import SessionLocal
from backend.models.db_models import VideoAnalysisResult

def cronbach_alpha(df):
    df = df.dropna()
    k = df.shape[1]
    if k < 2 or len(df) < 2:
        return np.nan
        
    item_variances = df.var(axis=0, ddof=1)
    total_variance = df.sum(axis=1).var(ddof=1)
    
    if total_variance == 0:
        return np.nan
        
    alpha = (k / (k - 1)) * (1 - (item_variances.sum() / total_variance))
    return alpha

def main():
    db = SessionLocal()
    results = db.query(VideoAnalysisResult).all()
    db.close()
    
    if not results:
        print("Belum ada data Video Analysis Result.")
        return
        
    data = []
    for r in results:
        data.append({
            # Mindful
            'gaze_score': r.gaze_score,
            'posture_score': r.posture_score,
            'silence_quality_score': r.silence_quality_score,
            
            # Meaningful
            'seating_score': r.seating_score,
            'talk_time_score': r.talk_time_score,
            'question_type_score': r.question_type_score,
            'teacher_movement_score': r.teacher_movement_score,
            
            # Joyful
            'expression_score': r.expression_score,
            'acoustic_score': r.acoustic_score,
            'collaboration_score': r.collaboration_score,
            'risk_taking_score': r.risk_taking_score,
        })
        
    df = pd.DataFrame(data)
    print(f"Total sesi video yang dianalisis: {len(df)}")
    
    # MINDFUL
    mindful_cols = ['gaze_score', 'posture_score', 'silence_quality_score']
    alpha_mindful = cronbach_alpha(df[mindful_cols])
    
    # MEANINGFUL
    meaningful_cols = ['seating_score', 'talk_time_score', 'teacher_movement_score']
    alpha_meaningful = cronbach_alpha(df[meaningful_cols])
    
    # JOYFUL
    joyful_cols = ['expression_score', 'acoustic_score', 'collaboration_score', 'risk_taking_score']
    alpha_joyful = cronbach_alpha(df[joyful_cols])
    
    print("\n=== HASIL CRONBACH'S ALPHA (Skor Prediksi Sistem CV) ===")
    print(f"1. MINDFUL    : {alpha_mindful:.4f} (Dari: {mindful_cols})")
    print(f"2. MEANINGFUL : {alpha_meaningful:.4f} (Dari: {meaningful_cols})")
    print(f"3. JOYFUL     : {alpha_joyful:.4f} (Dari: {joyful_cols})")
    print("======================================================")

if __name__ == "__main__":
    main()
