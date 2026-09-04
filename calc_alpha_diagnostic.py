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
    return (k / (k - 1)) * (1 - (item_variances.sum() / total_variance))

def alpha_if_item_deleted(df):
    """Hitung Alpha jika 1 item dihapus satu per satu."""
    results = {}
    for col in df.columns:
        remaining = df.drop(columns=[col])
        results[col] = cronbach_alpha(remaining)
    return results

def main():
    db = SessionLocal()
    results = db.query(VideoAnalysisResult).all()
    db.close()

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

    components = {
        'MINDFUL':     ['gaze_score', 'posture_score', 'silence_quality_score'],
        'MEANINGFUL':  ['seating_score', 'talk_time_score', 'teacher_movement_score'],
        'JOYFUL':      ['expression_score', 'acoustic_score', 'collaboration_score', 'risk_taking_score'],
    }

    thresholds = {
        'Sangat Buruk (< 0.0)': lambda a: a < 0,
        'Buruk (0.0-0.5)':      lambda a: 0 <= a < 0.5,
        'Cukup (0.5-0.7)':      lambda a: 0.5 <= a < 0.7,
        'Baik (0.7-0.9)':       lambda a: 0.7 <= a < 0.9,
        'Sangat Baik (>= 0.9)': lambda a: a >= 0.9,
    }

    def interpret(a):
        if np.isnan(a): return "Data tidak cukup"
        for label, fn in thresholds.items():
            if fn(a): return label
        return "?"

    print("=" * 65)
    print("   ANALISIS CRONBACH'S ALPHA + SARAN PERBAIKAN")
    print("=" * 65)

    for comp, cols in components.items():
        print(f"\n{'─'*65}")
        print(f"  KOMPONEN: {comp}")
        print(f"{'─'*65}")
        df_comp = df[cols]
        alpha = cronbach_alpha(df_comp)
        print(f"  Alpha saat ini : {alpha:.4f}  → {interpret(alpha)}")
        print()

        # Korelasi antar item
        print("  Korelasi antar sub-item:")
        corr_mat = df_comp.dropna().corr()
        for i, c1 in enumerate(cols):
            for j, c2 in enumerate(cols):
                if j > i:
                    val = corr_mat.loc[c1, c2]
                    flag = "⚠️ NEGATIF" if val < 0 else ("✅ OK" if val >= 0.3 else "⚡ LEMAH")
                    print(f"    {c1:30s} ↔ {c2:30s}: {val:+.3f} {flag}")
        print()

        # Alpha if item deleted
        print("  Alpha jika 1 item dihapus:")
        aid = alpha_if_item_deleted(df_comp)
        for item, a in sorted(aid.items(), key=lambda x: -x[1] if not np.isnan(x[1]) else -99):
            delta = a - alpha if not np.isnan(a) else float('nan')
            flag = "▲ NAIK (hapus item ini!)" if delta > 0.02 else ("▼ TURUN" if delta < -0.02 else "→ HAMPIR SAMA")
            print(f"    Hapus [{item:30s}] → Alpha = {a:.4f}  ({delta:+.4f} {flag})")

    print(f"\n{'=' * 65}")
    print("  REKOMENDASI BERDASARKAN DATA:")
    print(f"{'=' * 65}")
    print("""
  JOYFUL (Alpha = -0.0762, SANGAT BERMASALAH):
  ┌─────────────────────────────────────────────────────────────┐
  │ Masalah utama: acoustic_score berkorelasi NEGATIF kuat     │
  │ dengan risk_taking_score (-0.53) dan collaboration_score   │
  │ (-0.19).                                                   │
  │                                                            │
  │ Penyebab: acoustic_score menggabungkan RMS energy         │
  │ (kebisingan) dengan laughter/applause events. Di kelas    │
  │ yang aktif (risk-taking tinggi), kelas cenderung lebih    │
  │ gaduh sehingga RMS tinggi, tapi sistem mendeteksi ini     │
  │ sebagai "energetik" bukan "joyful".                       │
  │                                                            │
  │ SOLUSI TERBAIK (urut dari termudah):                      │
  │                                                            │
  │ 1. [TERMUDAH] Pisahkan acoustic_score menjadi 2 komponen: │
  │    - laughter_applause_score (events saja)                │
  │    - noise_score (energy)                                 │
  │    Gunakan hanya laughter_applause_score di Joyful.       │
  │                                                            │
  │ 2. [SEDANG] Turunkan bobot acoustic dari 0.30 → 0.15      │
  │    dan naikkan expression dari 0.30 → 0.45.              │
  │                                                            │
  │ 3. [TERBAIK] Redefine acoustic_score = HANYA              │
  │    (laughter_freq + applause_freq) tanpa komponen energy. │
  └─────────────────────────────────────────────────────────────┘

  MEANINGFUL (Alpha = 0.6720, CUKUP):
  ┌─────────────────────────────────────────────────────────────┐
  │ Sudah cukup baik. Untuk naik ke 0.7+:                     │
  │ - Cek apakah talk_time_score dan question_type_score      │
  │   sudah selaras. Jika guru sering bertanya (high          │
  │   question) tapi teacher_talk_pct juga tinggi, kedua      │
  │   metrik ini mungkin saling melemahkan.                   │
  └─────────────────────────────────────────────────────────────┘

  MINDFUL (Alpha = 0.7648, BAIK):
  ┌─────────────────────────────────────────────────────────────┐
  │ Sudah baik. Tidak perlu perubahan besar.                   │
  │ Untuk mempertahankan: pastikan silence_quality_score       │
  │ tidak selalu bernilai default 50.0 ketika audio gagal.    │
  └─────────────────────────────────────────────────────────────┘
""")

if __name__ == "__main__":
    main()
