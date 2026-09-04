import pandas as pd
from backend.database import SessionLocal
from backend.models.db_models import VideoAnalysisResult

db = SessionLocal()
results = db.query(VideoAnalysisResult).all()

data = [{
    'mindful': r.mindful_score, 
    'meaningful': r.meaningful_score, 
    'joyful': r.joyful_score, 
    'teacher_talk': r.teacher_talk_pct, 
    'student_talk': r.student_talk_pct
} for r in results]

df = pd.DataFrame(data)

print('=== DATA 3M & RASIO BICARA ===')
print(f'Total Sesi (Video): {len(df)}')
if len(df) > 0:
    print('\n1. Rata-rata Skor 3M dari semua sesi:')
    print(f'- Mindful: {df["mindful"].mean():.2f}')
    print(f'- Meaningful: {df["meaningful"].mean():.2f}')
    print(f'- Joyful: {df["joyful"].mean():.2f}')
    print('\n2. Rata-rata Rasio Bicara (Teacher vs Student):')
    print(f'- Teacher Talk: {df["teacher_talk"].mean():.2f}%')
    print(f'- Student Talk: {df["student_talk"].mean():.2f}%')
