import pandas as pd
import numpy as np
from backend.database import SessionLocal
from backend.models.ground_truth_models import GroundTruthAnnotation

def cronbach_alpha(df):
    # 1. Menghapus baris yang memiliki nilai NaN agar perhitungan valid
    df = df.dropna()
    k = df.shape[1]
    if k < 2:
        return np.nan
    if len(df) < 2:
        return np.nan
        
    # 2. Menghitung varians masing-masing item (kolom)
    item_variances = df.var(axis=0, ddof=1)
    
    # 3. Menghitung varians total (dari jumlah skor setiap baris)
    total_variance = df.sum(axis=1).var(ddof=1)
    
    if total_variance == 0:
        return np.nan
        
    # 4. Rumus Cronbach's Alpha
    alpha = (k / (k - 1)) * (1 - (item_variances.sum() / total_variance))
    return alpha

def main():
    db = SessionLocal()
    annotations = db.query(GroundTruthAnnotation).all()
    db.close()
    
    if not annotations:
        print("Belum ada data Ground Truth Annotations.")
        return
        
    data = []
    for a in annotations:
        data.append({
            'job_id': a.job_id,
            'annotator': a.annotator_name,
            # Mindful
            'gaze_on_task': a.gaze_on_task_ratio, # 0-1
            'posture_engaged': a.posture_engaged_ratio, # 0-1
            'mindful_score_gt': a.mindful_score_gt, # 0-100
            
            # Meaningful
            'teacher_talk_pct_gt': a.teacher_talk_pct_gt, # 0-100
            'meaningful_score_gt': a.meaningful_score_gt, # 0-100
            
            # Joyful
            'positive_expression': a.positive_expression_ratio, # 0-1
            'hand_raise_count': a.hand_raise_count, # absolut
            'joyful_score_gt': a.joyful_score_gt # 0-100
        })
        
    df = pd.DataFrame(data)
    print(f"Total baris data: {len(df)}")
    
    # Normalisasi Data (Scaling ke 0-100)
    if 'gaze_on_task' in df.columns:
        df['gaze_on_task_scaled'] = df['gaze_on_task'] * 100
    if 'posture_engaged' in df.columns:
        df['posture_engaged_scaled'] = df['posture_engaged'] * 100
    if 'positive_expression' in df.columns:
        df['positive_expression_scaled'] = df['positive_expression'] * 100
        
    # Karena hand_raise_count absolut (mungkin 0, 1, 2 dst), kita buat skala kira-kira.
    # Misalnya max hand raise adalah 10 -> kita asumsikan 10 itu 100%.
    if 'hand_raise_count' in df.columns and df['hand_raise_count'].notna().sum() > 0:
        max_hr = df['hand_raise_count'].max()
        if max_hr > 0:
            df['hand_raise_scaled'] = (df['hand_raise_count'] / max_hr) * 100
        else:
            df['hand_raise_scaled'] = 0
            
    # Kita harus berhati-hati, teacher_talk_pct_gt bisa jadi berkorelasi terbalik
    # dengan meaningful_score_gt tergantung rubrik. Kita biarkan as-is dulu.

    # 1. MINDFUL
    mindful_cols = ['gaze_on_task_scaled', 'posture_engaged_scaled', 'mindful_score_gt']
    df_mindful = df[mindful_cols]
    alpha_mindful = cronbach_alpha(df_mindful)
    
    # 2. MEANINGFUL
    meaningful_cols = ['teacher_talk_pct_gt', 'meaningful_score_gt']
    df_meaningful = df[meaningful_cols]
    alpha_meaningful = cronbach_alpha(df_meaningful)
    
    # 3. JOYFUL
    joyful_cols = ['positive_expression_scaled', 'hand_raise_scaled', 'joyful_score_gt']
    df_joyful = df[joyful_cols]
    alpha_joyful = cronbach_alpha(df_joyful)
    
    print("\n--- NILAI CRONBACH'S ALPHA SAAT INI ---")
    print(f"1. MINDFUL    : {alpha_mindful:.4f} (Menggunakan: {mindful_cols})")
    print(f"2. MEANINGFUL : {alpha_meaningful:.4f} (Menggunakan: {meaningful_cols})")
    print(f"3. JOYFUL     : {alpha_joyful:.4f} (Menggunakan: {joyful_cols})")

if __name__ == "__main__":
    main()
