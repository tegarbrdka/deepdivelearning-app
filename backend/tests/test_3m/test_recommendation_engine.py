# Feature: advanced-video-analysis-3m, Property 20: Recommendation Completeness
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from backend.ai.video_3m.aggregation.recommendation_engine import RecommendationEngine
from backend.ai.video_3m.data_models import AggregatedResult

def make_result(**kwargs):
    defaults = dict(mindful_score=70.0, meaningful_score=70.0, joyful_score=70.0, overall_3m_score=70.0, gaze_score=70.0, posture_score=70.0, silence_quality_score=70.0, seating_score=70.0, talk_time_score=70.0, question_type_score=70.0, teacher_movement_score=70.0, expression_score=70.0, acoustic_score=70.0, collaboration_score=70.0, risk_taking_score=70.0, teacher_talk_pct=35.0, student_talk_pct=55.0, silence_pct=10.0, meets_dl_standard=True, active_zone_ratio=0.70, laughter_events=[])
    defaults.update(kwargs)
    return AggregatedResult(**defaults)

@given(active_zone_ratio=st.floats(min_value=0.0, max_value=0.59, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_low_active_zone_triggers_movement_recommendation(active_zone_ratio):
    engine = RecommendationEngine()
    recs = engine.generate(make_result(active_zone_ratio=active_zone_ratio))
    keywords = ["pergerakan", "guru", "fasilitasi", "zona aktif", "kelompok"]
    has_rec = any(any(k in (r.get("title","") + r.get("description","")).lower() for k in keywords) for r in recs if r.get("aspect") == "meaningful")
    assert has_rec

@given(teacher_talk_pct=st.floats(min_value=40.01, max_value=100.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_high_teacher_talk_triggers_discussion_recommendation(teacher_talk_pct):
    engine = RecommendationEngine()
    recs = engine.generate(make_result(teacher_talk_pct=teacher_talk_pct, meets_dl_standard=False))
    keywords = ["diskusi", "siswa", "bicara", "dominasi"]
    has_rec = any(any(k in (r.get("title","") + r.get("description","")).lower() for k in keywords) for r in recs)
    assert has_rec

@given(joyful_score=st.floats(min_value=0.0, max_value=49.99, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_low_joyful_triggers_energy_recommendation(joyful_score):
    engine = RecommendationEngine()
    recs = engine.generate(make_result(joyful_score=joyful_score, expression_score=joyful_score, acoustic_score=joyful_score, collaboration_score=joyful_score, risk_taking_score=joyful_score))
    keywords = ["energi", "antusiasme", "joyful", "gamifikasi"]
    has_rec = any(any(k in (r.get("title","") + r.get("description","")).lower() for k in keywords) for r in recs if r.get("aspect") == "joyful")
    assert has_rec

def test_recommendations_ordered_by_severity():
    engine = RecommendationEngine()
    result = make_result(active_zone_ratio=0.10, joyful_score=35.0, expression_score=35.0, acoustic_score=35.0, collaboration_score=35.0, risk_taking_score=35.0, seating_score=40.0, question_type_score=40.0, mindful_score=80.0, gaze_score=80.0)
    recs = engine.generate(result)
    order = {"high": 0, "medium": 1, "low": 2, "positive": 3}
    severities = [order.get(r.get("severity", "low"), 99) for r in recs]
    assert severities == sorted(severities)

def test_each_recommendation_has_required_fields():
    engine = RecommendationEngine()
    result = make_result(active_zone_ratio=0.30, teacher_talk_pct=60.0, joyful_score=30.0, expression_score=30.0, acoustic_score=30.0, collaboration_score=30.0, risk_taking_score=30.0, question_type_score=30.0, seating_score=30.0)
    recs = engine.generate(result)
    required = {"aspect", "severity", "title", "description", "score"}
    for rec in recs:
        assert not (required - set(rec.keys()))
