# Feature: advanced-video-analysis-3m, Property 18: Triangulation Status Classification
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from backend.ai.video_3m.triangulation.cross_reference import CrossReferenceEngine
from backend.ai.video_3m.data_models import AggregatedResult, LessonPlan, PlannedActivity

ACTIVITY_TYPES = ["group_discussion", "mindful_reflection", "digital_gamification", "lecture"]

def make_analysis(**kwargs):
    defaults = dict(mindful_score=70.0, meaningful_score=70.0, joyful_score=70.0, overall_3m_score=70.0, gaze_score=70.0, posture_score=70.0, silence_quality_score=70.0, seating_score=70.0, talk_time_score=70.0, question_type_score=70.0, teacher_movement_score=70.0, expression_score=70.0, acoustic_score=70.0, collaboration_score=70.0, risk_taking_score=70.0, teacher_talk_pct=35.0, student_talk_pct=55.0, silence_pct=10.0, meets_dl_standard=True, active_zone_ratio=0.70, laughter_events=[1.0, 2.0])
    defaults.update(kwargs)
    return AggregatedResult(**defaults)

def test_alignment_score_is_success_ratio():
    engine = CrossReferenceEngine()
    activities = [PlannedActivity(activity_type="group_discussion", description="Diskusi kelompok"), PlannedActivity(activity_type="mindful_reflection", description="Refleksi")]
    lesson_plan = LessonPlan(activities=activities)
    analysis = make_analysis(seating_score=60.0, teacher_talk_pct=35.0, silence_quality_score=60.0, gaze_score=60.0)
    result = engine.compare(lesson_plan, analysis)
    success_count = sum(1 for it in result.items if it.status == "success")
    expected_score = (success_count / len(result.items)) * 100
    assert abs(result.alignment_score - expected_score) < 0.01

def test_empty_lesson_plan_returns_zero_alignment():
    engine = CrossReferenceEngine()
    lesson_plan = LessonPlan(activities=[])
    analysis = make_analysis()
    result = engine.compare(lesson_plan, analysis)
    assert result.alignment_score == 0.0
    assert result.items == []

def test_group_discussion_misalignment_when_teacher_dominates():
    engine = CrossReferenceEngine()
    activities = [PlannedActivity(activity_type="group_discussion", description="Diskusi kelompok")]
    lesson_plan = LessonPlan(activities=activities)
    analysis = make_analysis(teacher_talk_pct=60.0, seating_score=30.0)
    result = engine.compare(lesson_plan, analysis)
    assert len(result.items) == 1
    assert result.items[0].status == "misalignment"

def test_group_discussion_success_when_collaborative():
    engine = CrossReferenceEngine()
    activities = [PlannedActivity(activity_type="group_discussion", description="Diskusi kelompok")]
    lesson_plan = LessonPlan(activities=activities)
    analysis = make_analysis(teacher_talk_pct=35.0, seating_score=60.0)
    result = engine.compare(lesson_plan, analysis)
    assert len(result.items) == 1
    assert result.items[0].status == "success"

def test_digital_gamification_success_with_laughter():
    engine = CrossReferenceEngine()
    activities = [PlannedActivity(activity_type="digital_gamification", description="Quizizz")]
    lesson_plan = LessonPlan(activities=activities)
    analysis = make_analysis(laughter_events=[10.0, 20.0], joyful_score=60.0)
    result = engine.compare(lesson_plan, analysis)
    assert result.items[0].status == "success"

@given(n_activities=st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_alignment_score_in_range(n_activities):
    engine = CrossReferenceEngine()
    activities = [PlannedActivity(activity_type="group_discussion", description=f"Activity {i}") for i in range(n_activities)]
    lesson_plan = LessonPlan(activities=activities)
    analysis = make_analysis()
    result = engine.compare(lesson_plan, analysis)
    assert 0.0 <= result.alignment_score <= 100.0

@given(n_activities=st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_item_count_matches_activity_count(n_activities):
    engine = CrossReferenceEngine()
    activities = [PlannedActivity(activity_type="group_discussion", description=f"Activity {i}") for i in range(n_activities)]
    lesson_plan = LessonPlan(activities=activities)
    analysis = make_analysis()
    result = engine.compare(lesson_plan, analysis)
    assert len(result.items) == n_activities

def test_all_items_have_valid_status():
    engine = CrossReferenceEngine()
    activities = [PlannedActivity(activity_type=t, description=t) for t in ACTIVITY_TYPES]
    lesson_plan = LessonPlan(activities=activities)
    analysis = make_analysis()
    result = engine.compare(lesson_plan, analysis)
    valid_statuses = {"success", "misalignment", "not_detected"}
    for item in result.items:
        assert item.status in valid_statuses, f"Invalid status: {item.status}"
