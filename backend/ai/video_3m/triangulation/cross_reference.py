"""
CrossReferenceEngine — compares planned RPP activities against video analysis results
to detect alignments and misalignments.
"""
from __future__ import annotations
from typing import List

from backend.ai.video_3m.data_models import (
    LessonPlan,
    AggregatedResult,
    TriangulationItem,
    TriangulationResult,
)


class CrossReferenceEngine:
    """
    Compares a parsed LessonPlan against an AggregatedResult to produce
    a TriangulationResult with per-activity alignment status and recommendations.
    """

    def compare(
        self, lesson_plan: LessonPlan, analysis: AggregatedResult
    ) -> TriangulationResult:
        """
        For each planned activity, check if video evidence supports it.
        Returns TriangulationResult with items and overall alignment_score.
        """
        if not lesson_plan.activities:
            return TriangulationResult(items=[], alignment_score=0.0)

        items: List[TriangulationItem] = []

        for activity in lesson_plan.activities:
            item = self._evaluate_activity(activity.activity_type, activity.description, analysis)
            items.append(item)

        success_count = sum(1 for it in items if it.status == "success")
        alignment_score = round((success_count / len(items)) * 100, 2) if items else 0.0

        return TriangulationResult(items=items, alignment_score=alignment_score)

    # ------------------------------------------------------------------
    # Private: Per-activity evaluation
    # ------------------------------------------------------------------

    def _evaluate_activity(
        self, activity_type: str, description: str, analysis: AggregatedResult
    ) -> TriangulationItem:
        """Evaluate a single planned activity against the analysis result."""

        if activity_type == "group_discussion":
            return self._check_group_discussion(description, analysis)
        elif activity_type == "mindful_reflection":
            return self._check_mindful_reflection(description, analysis)
        elif activity_type == "digital_gamification":
            return self._check_digital_gamification(description, analysis)
        elif activity_type == "lecture":
            return self._check_lecture(description, analysis)
        elif activity_type == "peer_discussion":
            return self._check_peer_discussion(description, analysis)
        elif activity_type == "hands_on_activity":
            return self._check_hands_on(description, analysis)
        else:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=False,
                status="not_detected",
                evidence="Tipe aktivitas tidak dikenali oleh sistem.",
                recommendation="",
            )

    def _check_group_discussion(
        self, description: str, analysis: AggregatedResult
    ) -> TriangulationItem:
        """
        group_discussion planned but students in rows with teacher talk > 50%: misalignment.
        group_discussion planned and seating_score high + teacher_talk_pct <= 50%: success.
        """
        # Detect misalignment: teacher dominates talk AND seating is not collaborative
        teacher_dominates = analysis.teacher_talk_pct > 50.0
        low_seating = analysis.seating_score < 50.0

        if teacher_dominates and low_seating:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=False,
                status="misalignment",
                evidence=(
                    f"Guru berbicara {analysis.teacher_talk_pct:.1f}% dari waktu "
                    f"dan formasi tempat duduk tidak kolaboratif (skor: {analysis.seating_score:.0f}/100)."
                ),
                recommendation=(
                    "Ubah formasi tempat duduk ke kelompok atau lingkaran dan berikan lebih banyak "
                    "waktu diskusi kepada siswa. Target: guru berbicara ≤40%, siswa ≥60%."
                ),
            )
        elif analysis.seating_score >= 50.0 and not teacher_dominates:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=True,
                status="success",
                evidence=(
                    f"Formasi tempat duduk kolaboratif terdeteksi (skor: {analysis.seating_score:.0f}/100) "
                    f"dengan porsi bicara siswa {analysis.student_talk_pct:.1f}%."
                ),
                recommendation="",
            )
        else:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=False,
                status="not_detected",
                evidence="Bukti diskusi kelompok tidak cukup terdeteksi dalam video.",
                recommendation=(
                    "Pastikan siswa ditempatkan dalam kelompok dan diberikan tugas diskusi yang jelas."
                ),
            )

    def _check_mindful_reflection(
        self, description: str, analysis: AggregatedResult
    ) -> TriangulationItem:
        """
        mindful_reflection planned and silence period detected with high gaze score: success.
        """
        has_reflection = analysis.silence_quality_score >= 50.0
        high_gaze = analysis.gaze_score >= 50.0

        if has_reflection and high_gaze:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=True,
                status="success",
                evidence=(
                    f"Periode refleksi terdeteksi dengan kualitas keheningan {analysis.silence_quality_score:.0f}/100 "
                    f"dan fokus pandangan siswa {analysis.gaze_score:.0f}/100."
                ),
                recommendation="",
            )
        elif has_reflection or high_gaze:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=True,
                status="success",
                evidence=(
                    f"Indikasi refleksi terdeteksi: keheningan {analysis.silence_quality_score:.0f}/100, "
                    f"fokus {analysis.gaze_score:.0f}/100."
                ),
                recommendation="Tingkatkan kualitas sesi STOP/refleksi agar lebih terstruktur.",
            )
        else:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=False,
                status="not_detected",
                evidence="Tidak terdeteksi periode keheningan reflektif yang signifikan dalam video.",
                recommendation=(
                    "Tambahkan sesi STOP (Still, Think, Observe, Plan) yang eksplisit "
                    "dengan durasi minimal 2–3 menit."
                ),
            )

    def _check_digital_gamification(
        self, description: str, analysis: AggregatedResult
    ) -> TriangulationItem:
        """
        digital_gamification planned and laughter/enthusiasm detected: success.
        """
        has_laughter = len(analysis.laughter_events) > 0
        high_acoustic = analysis.acoustic_score >= 50.0
        high_joyful = analysis.joyful_score >= 50.0

        if has_laughter or (high_acoustic and high_joyful):
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=True,
                status="success",
                evidence=(
                    f"Antusiasme terdeteksi: {len(analysis.laughter_events)} momen tawa, "
                    f"skor Joyful {analysis.joyful_score:.0f}/100."
                ),
                recommendation="",
            )
        else:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=False,
                status="not_detected",
                evidence=(
                    f"Tidak terdeteksi antusiasme yang cukup untuk gamifikasi digital "
                    f"(skor Joyful: {analysis.joyful_score:.0f}/100)."
                ),
                recommendation=(
                    "Pastikan aktivitas gamifikasi melibatkan seluruh siswa dan berikan "
                    "umpan balik langsung yang memotivasi."
                ),
            )

    def _check_lecture(
        self, description: str, analysis: AggregatedResult
    ) -> TriangulationItem:
        """
        lecture planned and teacher_talk_pct is high: success (but flag if too high).
        """
        if analysis.teacher_talk_pct >= 40.0:
            if analysis.teacher_talk_pct > 60.0:
                return TriangulationItem(
                    activity=description,
                    planned=True,
                    detected=True,
                    status="misalignment",
                    evidence=(
                        f"Ceramah terdeteksi namun guru mendominasi {analysis.teacher_talk_pct:.1f}% "
                        "waktu, melebihi standar Deep Learning."
                    ),
                    recommendation=(
                        "Kurangi porsi ceramah dan tambahkan aktivitas interaktif. "
                        "Target standar Deep Learning: guru ≤40%, siswa ≥60%."
                    ),
                )
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=True,
                status="success",
                evidence=(
                    f"Ceramah terdeteksi dengan porsi guru {analysis.teacher_talk_pct:.1f}% "
                    "sesuai standar Deep Learning."
                ),
                recommendation="",
            )
        else:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=False,
                status="not_detected",
                evidence=(
                    f"Porsi bicara guru sangat rendah ({analysis.teacher_talk_pct:.1f}%), "
                    "ceramah tidak terdeteksi secara signifikan."
                ),
                recommendation="",
            )

    def _check_peer_discussion(
        self, description: str, analysis: AggregatedResult
    ) -> TriangulationItem:
        """Peer discussion: high student talk + collaborative seating."""
        high_student_talk = analysis.student_talk_pct >= 50.0
        collaborative_seating = analysis.seating_score >= 40.0

        if high_student_talk and collaborative_seating:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=True,
                status="success",
                evidence=(
                    f"Diskusi antar siswa terdeteksi: siswa berbicara {analysis.student_talk_pct:.1f}% "
                    f"dengan formasi kolaboratif (skor: {analysis.seating_score:.0f}/100)."
                ),
                recommendation="",
            )
        else:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=False,
                status="not_detected",
                evidence="Bukti diskusi antar siswa tidak cukup terdeteksi.",
                recommendation=(
                    "Gunakan strategi Think-Pair-Share atau berpasangan untuk mendorong "
                    "interaksi antar siswa."
                ),
            )

    def _check_hands_on(
        self, description: str, analysis: AggregatedResult
    ) -> TriangulationItem:
        """Hands-on activity: high collaboration + movement."""
        high_collab = analysis.collaboration_score >= 50.0
        active_movement = analysis.active_zone_ratio >= 0.40

        if high_collab or active_movement:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=True,
                status="success",
                evidence=(
                    f"Aktivitas langsung terdeteksi: kolaborasi {analysis.collaboration_score:.0f}/100, "
                    f"pergerakan aktif {analysis.active_zone_ratio * 100:.0f}%."
                ),
                recommendation="",
            )
        else:
            return TriangulationItem(
                activity=description,
                planned=True,
                detected=False,
                status="not_detected",
                evidence="Aktivitas langsung/praktikum tidak terdeteksi secara signifikan.",
                recommendation=(
                    "Pastikan siswa terlibat aktif secara fisik dalam kegiatan praktikum atau proyek."
                ),
            )
