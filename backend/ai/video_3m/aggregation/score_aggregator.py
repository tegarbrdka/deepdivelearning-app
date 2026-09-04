"""
ScoreAggregator — combines per-fragment results into final 3M scores.
"""
from __future__ import annotations
from typing import List
import numpy as np

from backend.ai.video_3m.data_models import FragmentAnalysis, AggregatedResult


class ScoreAggregator:
    # Mindful sub-score weights
    MINDFUL_WEIGHTS = {
        "gaze": 0.40,
        "posture": 0.35,
        "silence_quality": 0.25,
    }
    # Meaningful sub-score weights
    MEANINGFUL_WEIGHTS = {
        "seating": 0.30,
        "talk_time": 0.40,
        "teacher_movement": 0.30,
    }
    # Joyful sub-score weights
    JOYFUL_WEIGHTS = {
        "expression": 0.30,
        "acoustic": 0.30,
        "collaboration": 0.25,
        "risk_taking": 0.15,
    }
    # Overall 3M weights
    OVERALL_WEIGHTS = {
        "mindful": 0.33,
        "meaningful": 0.34,
        "joyful": 0.33,
    }

    def aggregate(self, fragment_results: List[FragmentAnalysis]) -> AggregatedResult:
        """
        Compute simple mean of each sub-score across all fragments,
        then apply weighted combination to produce composite 3M scores.
        """
        if not fragment_results:
            return AggregatedResult()

        # Collect per-fragment sub-scores
        gaze_scores, posture_scores, silence_scores = [], [], []
        seating_scores, talk_time_scores, question_scores, movement_scores = [], [], [], []
        expression_scores, acoustic_scores, collab_scores, risk_scores = [], [], [], []
        teacher_talk_pcts, student_talk_pcts, silence_pcts = [], [], []
        active_zone_ratios = []
        aha_moments, laughter_events, applause_events = [], [], []
        seating_transitions = []
        heatmap_accumulator = None
        max_discussion_groups = 0

        for fa in fragment_results:
            m = fa.mindful
            mn = fa.meaningful
            j = fa.joyful

            gaze_scores.append(m.gaze_score)
            posture_scores.append(m.posture_score)
            silence_scores.append(m.silence_quality_score)

            seating_scores.append(mn.seating_score)
            talk_time_scores.append(mn.talk_time_score)
            question_scores.append(mn.question_type_score)
            movement_scores.append(mn.teacher_movement_score)
            active_zone_ratios.append(mn.active_zone_ratio)

            # Track max discussion groups across all fragments
            if hasattr(mn, 'discussion_groups_count') and mn.discussion_groups_count > max_discussion_groups:
                max_discussion_groups = mn.discussion_groups_count

            if mn.talk_time_ratio:
                teacher_talk_pcts.append(mn.talk_time_ratio.teacher_pct)
                student_talk_pcts.append(mn.talk_time_ratio.student_pct)
                silence_pcts.append(mn.talk_time_ratio.silence_pct)

            expression_scores.append(j.expression_score)
            acoustic_scores.append(j.acoustic_score)
            collab_scores.append(j.collaboration_score)
            risk_scores.append(j.risk_taking_score)

            aha_moments.extend(j.aha_moments)
            laughter_events.extend(j.laughter_events)
            applause_events.extend(j.applause_events)

            for se in mn.seating_formations:
                seating_transitions.append({
                    "timestamp_sec": se.timestamp_sec,
                    "formation": se.formation,
                })

            # Accumulate heatmap grids
            if j.heatmap_data:
                grid = np.array(j.heatmap_data)
                if heatmap_accumulator is None:
                    heatmap_accumulator = grid.copy()
                else:
                    if heatmap_accumulator.shape == grid.shape:
                        heatmap_accumulator += grid

        def mean(lst): return round(float(np.mean(lst)), 2) if lst else 0.0

        # Composite scores
        gaze_score = mean(gaze_scores)
        posture_score = mean(posture_scores)
        silence_quality_score = mean(silence_scores)
        mindful_score = round(
            self.MINDFUL_WEIGHTS["gaze"] * gaze_score
            + self.MINDFUL_WEIGHTS["posture"] * posture_score
            + self.MINDFUL_WEIGHTS["silence_quality"] * silence_quality_score,
            2,
        )

        seating_score = mean(seating_scores)
        talk_time_score = mean(talk_time_scores)
        question_type_score = mean(question_scores)
        teacher_movement_score = mean(movement_scores)
        meaningful_score = round(
            self.MEANINGFUL_WEIGHTS["seating"] * seating_score
            + self.MEANINGFUL_WEIGHTS["talk_time"] * talk_time_score
            + self.MEANINGFUL_WEIGHTS["teacher_movement"] * teacher_movement_score,
            2,
        )

        expression_score = mean(expression_scores)
        acoustic_score = mean(acoustic_scores)
        collaboration_score = mean(collab_scores)
        risk_taking_score = mean(risk_scores)
        joyful_score = round(
            self.JOYFUL_WEIGHTS["expression"] * expression_score
            + self.JOYFUL_WEIGHTS["acoustic"] * acoustic_score
            + self.JOYFUL_WEIGHTS["collaboration"] * collaboration_score
            + self.JOYFUL_WEIGHTS["risk_taking"] * risk_taking_score,
            2,
        )

        overall_3m_score = round(
            self.OVERALL_WEIGHTS["mindful"] * mindful_score
            + self.OVERALL_WEIGHTS["meaningful"] * meaningful_score
            + self.OVERALL_WEIGHTS["joyful"] * joyful_score,
            2,
        )

        # Talk-time averages
        teacher_talk_pct = mean(teacher_talk_pcts) if teacher_talk_pcts else 0.0
        student_talk_pct = mean(student_talk_pcts) if student_talk_pcts else 0.0
        silence_pct = mean(silence_pcts) if silence_pcts else 0.0
        meets_dl_standard = (30.0 <= teacher_talk_pct <= 40.0) and (60.0 <= student_talk_pct <= 70.0)
        active_zone_ratio = mean(active_zone_ratios)

        # Timeline data (per-fragment scores ordered by start_sec)
        timeline_data = []
        for fa in sorted(fragment_results, key=lambda x: x.fragment.start_sec):
            frag = fa.fragment
            timeline_data.append({
                "index": frag.index,
                "start_sec": frag.start_sec,
                "end_sec": frag.end_sec,
                "label": f"{int(frag.start_sec // 60)}:{int(frag.start_sec % 60):02d} – "
                         f"{int(frag.end_sec // 60)}:{int(frag.end_sec % 60):02d}",
                "mindful": fa.mindful.mindful_score,
                "meaningful": fa.meaningful.meaningful_score,
                "joyful": fa.joyful.joyful_score,
                "seating_formation": fa.meaningful.seating_formations[-1].formation
                    if fa.meaningful.seating_formations else "unknown",
                "active_zone_ratio": fa.meaningful.active_zone_ratio,
                "teacher_talk_pct": fa.meaningful.talk_time_ratio.teacher_pct
                    if fa.meaningful.talk_time_ratio else 0.0,
                "student_talk_pct": fa.meaningful.talk_time_ratio.student_pct
                    if fa.meaningful.talk_time_ratio else 0.0,
            })

        # Normalize accumulated heatmap
        heatmap_data: list = []
        if heatmap_accumulator is not None:
            max_val = heatmap_accumulator.max()
            if max_val > 0:
                heatmap_accumulator = heatmap_accumulator / max_val
            heatmap_data = heatmap_accumulator.tolist()

        return AggregatedResult(
            mindful_score=mindful_score,
            meaningful_score=meaningful_score,
            joyful_score=joyful_score,
            overall_3m_score=overall_3m_score,
            gaze_score=gaze_score,
            posture_score=posture_score,
            silence_quality_score=silence_quality_score,
            seating_score=seating_score,
            talk_time_score=talk_time_score,
            question_type_score=question_type_score,
            teacher_movement_score=teacher_movement_score,
            expression_score=expression_score,
            acoustic_score=acoustic_score,
            collaboration_score=collaboration_score,
            risk_taking_score=risk_taking_score,
            teacher_talk_pct=teacher_talk_pct,
            student_talk_pct=student_talk_pct,
            silence_pct=silence_pct,
            meets_dl_standard=meets_dl_standard,
            active_zone_ratio=active_zone_ratio,
            timeline_data=timeline_data,
            heatmap_data=heatmap_data,
            aha_moments=sorted(aha_moments),
            laughter_events=sorted(laughter_events),
            applause_events=sorted(applause_events),
            seating_transitions=seating_transitions,
            total_fragments=len(fragment_results),
            discussion_groups_count=max_discussion_groups,
        )
