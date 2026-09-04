import json
import numpy as np
from backend.database import SessionLocal
from backend.models.db_models import VideoAnalysisResult, VideoAnalysisJob

def main():
    db = SessionLocal()
    results = db.query(VideoAnalysisResult).all()
    
    print(f"Mengupdate {len(results)} data historis...")
    
    for r in results:
        # 1. Dapatkan durasi video dari job
        job = db.query(VideoAnalysisJob).filter(VideoAnalysisJob.job_id == r.job_id).first()
        duration_sec = job.video_duration_sec if (job and job.video_duration_sec) else 300.0
        duration_min = duration_sec / 60.0
        
        # 2. Ambil event tawa & tepuk tangan
        laughter = r.laughter_events if r.laughter_events else []
        applause = r.applause_events if r.applause_events else []
        if isinstance(laughter, str):
            laughter = json.loads(laughter)
        if isinstance(applause, str):
            applause = json.loads(applause)
            
        # 3. Hitung frekuensi baru
        laughter_freq = len(laughter) / max(duration_min, 0.01)
        applause_freq = len(applause) / max(duration_min, 0.01)
        
        # 4. Hitung ulang acoustic_score dengan formula baru (hanya event frequency)
        new_acoustic = round(min(100.0, (laughter_freq + applause_freq) * 10.0), 2)
        
        # Simpan nilai lama untuk log
        old_acoustic = r.acoustic_score
        old_joyful = r.joyful_score
        old_meaningful = r.meaningful_score
        old_overall = r.overall_3m_score
        
        # 5. Update field pada model
        r.acoustic_score = new_acoustic
        
        # 6. Hitung ulang meaningful_score (bobot baru: 0.30 seating, 0.40 talk_time, 0.30 movement)
        r.meaningful_score = round(
            0.30 * (r.seating_score or 0.0)
            + 0.40 * (r.talk_time_score or 0.0)
            + 0.30 * (r.teacher_movement_score or 0.0),
            2
        )
        
        # 7. Hitung ulang joyful_score
        # Formula: 0.30*expression + 0.30*acoustic + 0.25*collab + 0.15*risk_taking
        r.joyful_score = round(
            0.30 * (r.expression_score or 0.0)
            + 0.30 * new_acoustic
            + 0.25 * (r.collaboration_score or 0.0)
            + 0.15 * (r.risk_taking_score or 0.0),
            2
        )
        
        # 8. Hitung ulang overall_3m_score
        # Formula: 0.33*mindful + 0.34*meaningful + 0.33*joyful
        r.overall_3m_score = round(
            0.33 * (r.mindful_score or 0.0)
            + 0.34 * r.meaningful_score
            + 0.33 * r.joyful_score,
            2
        )
        
        print(f"ID {r.id:2d} | Meaningful: {old_meaningful:5.2f} -> {r.meaningful_score:5.2f} | Joyful: {old_joyful:5.2f} -> {r.joyful_score:5.2f} | Overall: {old_overall:5.2f} -> {r.overall_3m_score:5.2f}")
        
    db.commit()
    db.close()
    print("Database berhasil diperbarui dengan formula baru!")

if __name__ == "__main__":
    main()
