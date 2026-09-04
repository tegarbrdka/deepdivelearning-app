import pandas as pd
from backend.database import SessionLocal
from backend.models.ground_truth_models import GroundTruthAnnotation

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
            'gaze_on_task': a.gaze_on_task_ratio,
            'posture_engaged': a.posture_engaged_ratio,
            'mindful_score_gt': a.mindful_score_gt,
            'teacher_talk_pct_gt': a.teacher_talk_pct_gt,
            'meaningful_score_gt': a.meaningful_score_gt,
            'positive_expression': a.positive_expression_ratio,
            'hand_raise_count': a.hand_raise_count,
            'joyful_score_gt': a.joyful_score_gt
        })
        
    df = pd.DataFrame(data)
    
    # Lakukan scaling (normalisasi 0-100) persis seperti di calc_alpha.py
    df['gaze_on_task_scaled'] = df['gaze_on_task'] * 100
    df['posture_engaged_scaled'] = df['posture_engaged'] * 100
    df['positive_expression_scaled'] = df['positive_expression'] * 100
    
    if df['hand_raise_count'].notna().sum() > 0:
        max_hr = df['hand_raise_count'].max()
        df['hand_raise_scaled'] = (df['hand_raise_count'] / max_hr) * 100 if max_hr > 0 else 0
    else:
        df['hand_raise_scaled'] = 0
        
    # Pilih kolom yang sudah discaling agar siap dinilai dosen
    final_df = df[[
        'job_id', 'annotator',
        'gaze_on_task_scaled', 'posture_engaged_scaled', 'mindful_score_gt',
        'teacher_talk_pct_gt', 'meaningful_score_gt',
        'positive_expression_scaled', 'hand_raise_scaled', 'joyful_score_gt'
    ]]
    
    final_df.to_csv("tabulasi_data_mentah_cronbach.csv", index=False)
    print("Berhasil! File tabulasi_data_mentah_cronbach.csv telah dibuat.")

if __name__ == "__main__":
    main()
