"""
RecommendationEngine — generates actionable recommendations from 3M scores.
"""
from __future__ import annotations
from typing import List

from backend.ai.video_3m.data_models import AggregatedResult


class RecommendationEngine:
    """
    Generates prioritized, actionable recommendations based on detected
    strengths and weaknesses in the 3M analysis results.
    """

    def generate(self, result: AggregatedResult) -> List[dict]:
        """
        Returns a list of recommendation dicts ordered by severity (highest first).
        Each dict: {aspect, severity, title, description, score}
        """
        recommendations: List[dict] = []

        # --- Meaningful: Teacher Movement ---
        if result.active_zone_ratio < 0.60:
            severity = self._severity(result.active_zone_ratio, low=0.30, high=0.60)
            recommendations.append({
                "aspect": "meaningful",
                "severity": severity,
                "title": "Tingkatkan Pergerakan Guru",
                "description": (
                    "Guru menghabiskan sebagian besar waktu di zona statis (depan kelas). "
                    "Tingkatkan pergerakan di antara kelompok siswa untuk memfasilitasi, "
                    "bukan ceramah. Target: >60% waktu di zona aktif."
                ),
                "score": round(result.active_zone_ratio * 100, 1),
            })

        # --- Meaningful: Talk-Time Ratio ---
        if result.teacher_talk_pct > 40.0:
            excess = result.teacher_talk_pct - 40.0
            severity = "high" if excess > 20 else "medium"
            recommendations.append({
                "aspect": "meaningful",
                "severity": severity,
                "title": "Kurangi Dominasi Bicara Guru",
                "description": (
                    f"Guru berbicara {result.teacher_talk_pct:.1f}% dari waktu "
                    f"(standar Deep Learning: 30-40%). "
                    "Berikan lebih banyak kesempatan diskusi kepada siswa melalui "
                    "pertanyaan terbuka dan aktivitas kelompok."
                ),
                "score": round(result.teacher_talk_pct, 1),
            })

        # --- Joyful: Low energy ---
        if result.joyful_score < 50.0:
            severity = self._severity(result.joyful_score, low=25.0, high=50.0)
            recommendations.append({
                "aspect": "joyful",
                "severity": severity,
                "title": "Tingkatkan Energi dan Antusiasme Kelas",
                "description": (
                    "Indikator Joyful rendah. Pertimbangkan gamifikasi, aktivitas fisik, "
                    "atau ice-breaker untuk meningkatkan energi kelas dan ekspresi positif siswa."
                ),
                "score": round(result.joyful_score, 1),
            })

        # --- Meaningful: Question Type ---
        if result.question_type_score < 50.0:
            severity = self._severity(result.question_type_score, low=25.0, high=50.0)
            recommendations.append({
                "aspect": "meaningful",
                "severity": severity,
                "title": "Gunakan Lebih Banyak Pertanyaan Pemantik",
                "description": (
                    "Pertanyaan guru didominasi oleh perintah instruksional. "
                    "Gunakan lebih banyak pertanyaan pemantik seperti 'Mengapa...', "
                    "'Bagaimana jika...', 'Menurutmu...' untuk mendorong berpikir kritis."
                ),
                "score": round(result.question_type_score, 1),
            })

        # --- Meaningful: Seating ---
        if result.seating_score < 50.0:
            severity = self._severity(result.seating_score, low=25.0, high=50.0)
            recommendations.append({
                "aspect": "meaningful",
                "severity": severity,
                "title": "Ubah Formasi Tempat Duduk",
                "description": (
                    "Siswa duduk dalam formasi baris tradisional sepanjang pelajaran. "
                    "Transisikan ke formasi kelompok kecil atau lingkaran untuk "
                    "mendorong kolaborasi dan diskusi antar siswa."
                ),
                "score": round(result.seating_score, 1),
            })

        # --- Mindful: Low gaze/focus ---
        if result.gaze_score < 50.0:
            severity = self._severity(result.gaze_score, low=25.0, high=50.0)
            recommendations.append({
                "aspect": "mindful",
                "severity": severity,
                "title": "Tingkatkan Fokus dan Kesadaran Siswa",
                "description": (
                    "Deteksi menunjukkan banyak siswa tidak fokus ke materi/guru. "
                    "Pertimbangkan aktivitas STOP (refleksi singkat), variasi metode, "
                    "atau cek pemahaman lebih sering."
                ),
                "score": round(result.gaze_score, 1),
            })

        # --- Positive reinforcement ---
        if result.mindful_score >= 70.0:
            recommendations.append({
                "aspect": "mindful",
                "severity": "positive",
                "title": "Praktik Mindful Sangat Kuat",
                "description": (
                    f"Skor Mindful {result.mindful_score:.1f}/100. "
                    "Siswa menunjukkan fokus dan kesadaran yang tinggi. Pertahankan!"
                ),
                "score": round(result.mindful_score, 1),
            })

        if result.joyful_score >= 70.0:
            recommendations.append({
                "aspect": "joyful",
                "severity": "positive",
                "title": "Iklim Kelas Sangat Positif",
                "description": (
                    f"Skor Joyful {result.joyful_score:.1f}/100. "
                    "Terdeteksi antusiasme, tawa, dan kolaborasi aktif. Luar biasa!"
                ),
                "score": round(result.joyful_score, 1),
            })

        # Sort: high severity first, then medium, then low, then positive
        severity_order = {"high": 0, "medium": 1, "low": 2, "positive": 3}
        recommendations.sort(key=lambda r: severity_order.get(r["severity"], 99))

        return recommendations

    def _severity(self, score: float, low: float, high: float) -> str:
        """Map a score to severity level based on thresholds."""
        if score < low:
            return "high"
        elif score < high:
            return "medium"
        return "low"
