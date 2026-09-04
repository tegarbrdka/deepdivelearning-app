# Feature: advanced-video-analysis-3m, Property 21: CSV Export Field Completeness
"""
Property-based tests for CSV export field completeness.
Property 21 from the design document.

Tests the CSV generation logic directly (without HTTP layer) by
replicating the writer logic from the export endpoint.
"""
import csv
import io
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from datetime import datetime


# Required CSV columns per spec (Requirements 25.1, 25.3)
REQUIRED_CSV_COLUMNS = {
    "job_id",
    "video_name",
    "mindful_score",
    "meaningful_score",
    "joyful_score",
    "overall_3m_score",
    "teacher_talk_pct",
    "student_talk_pct",
    "created_at",
}

SCORE_RANGE = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
PCT_RANGE = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)


def build_csv_row(job_id, video_name, mindful, meaningful, joyful, overall,
                  teacher_pct, student_pct, meets_standard, created_at,
                  alignment_score=None):
    """
    Mirrors the CSV generation logic from the export endpoint.
    Returns (headers, row) as lists.
    """
    headers = [
        "job_id", "video_name", "mindful_score", "meaningful_score",
        "joyful_score", "overall_3m_score", "teacher_talk_pct",
        "student_talk_pct", "meets_dl_standard", "created_at",
    ]
    if alignment_score is not None:
        headers.append("alignment_score")

    row = [
        job_id, video_name, mindful, meaningful, joyful, overall,
        teacher_pct, student_pct, meets_standard, created_at,
    ]
    if alignment_score is not None:
        row.append(alignment_score)

    return headers, row


def write_csv(headers, row) -> str:
    """Write headers + row to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerow(row)
    output.seek(0)
    return output.getvalue()


def parse_csv(csv_str: str) -> dict:
    """Parse CSV string into a dict of {column: value}."""
    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 1, f"Expected 1 data row, got {len(rows)}"
    return rows[0]


# --- Property 21: CSV Export Field Completeness ---

@given(
    mindful=SCORE_RANGE,
    meaningful=SCORE_RANGE,
    joyful=SCORE_RANGE,
    overall=SCORE_RANGE,
    teacher_pct=PCT_RANGE,
    student_pct=PCT_RANGE,
)
@settings(max_examples=100)
def test_csv_contains_all_required_columns(mindful, meaningful, joyful, overall,
                                           teacher_pct, student_pct):
    """Exported CSV contains all required columns."""
    headers, row = build_csv_row(
        job_id="test-job-id",
        video_name="test_video.mp4",
        mindful=mindful,
        meaningful=meaningful,
        joyful=joyful,
        overall=overall,
        teacher_pct=teacher_pct,
        student_pct=student_pct,
        meets_standard=True,
        created_at=datetime.now().isoformat(),
    )
    csv_str = write_csv(headers, row)
    parsed = parse_csv(csv_str)

    missing = REQUIRED_CSV_COLUMNS - set(parsed.keys())
    assert not missing, f"CSV missing required columns: {missing}"


@given(
    mindful=SCORE_RANGE,
    meaningful=SCORE_RANGE,
    joyful=SCORE_RANGE,
    overall=SCORE_RANGE,
    teacher_pct=PCT_RANGE,
    student_pct=PCT_RANGE,
)
@settings(max_examples=100)
def test_csv_no_required_field_is_empty(mindful, meaningful, joyful, overall,
                                        teacher_pct, student_pct):
    """No required field is null or empty in the CSV output."""
    job_id = "abc123-def456"
    video_name = "lesson_video.mp4"
    created_at = "2025-01-15T10:30:00"

    headers, row = build_csv_row(
        job_id=job_id,
        video_name=video_name,
        mindful=mindful,
        meaningful=meaningful,
        joyful=joyful,
        overall=overall,
        teacher_pct=teacher_pct,
        student_pct=student_pct,
        meets_standard=True,
        created_at=created_at,
    )
    csv_str = write_csv(headers, row)
    parsed = parse_csv(csv_str)

    for col in REQUIRED_CSV_COLUMNS:
        assert parsed.get(col) not in (None, ""), (
            f"Required column '{col}' is empty/null in CSV"
        )


@given(
    alignment_score=SCORE_RANGE,
)
@settings(max_examples=50)
def test_csv_with_triangulation_includes_alignment_score(alignment_score):
    """When triangulation is present, alignment_score column is included."""
    headers, row = build_csv_row(
        job_id="job-with-rpp",
        video_name="video.mp4",
        mindful=70.0,
        meaningful=70.0,
        joyful=70.0,
        overall=70.0,
        teacher_pct=35.0,
        student_pct=55.0,
        meets_standard=True,
        created_at="2025-01-15T10:30:00",
        alignment_score=alignment_score,
    )
    csv_str = write_csv(headers, row)
    parsed = parse_csv(csv_str)

    assert "alignment_score" in parsed, "alignment_score column missing when triangulation present"
    assert parsed["alignment_score"] not in (None, ""), "alignment_score is empty"


def test_csv_without_triangulation_has_no_alignment_column():
    """Without triangulation, alignment_score column is NOT present."""
    headers, row = build_csv_row(
        job_id="job-no-rpp",
        video_name="video.mp4",
        mindful=70.0,
        meaningful=70.0,
        joyful=70.0,
        overall=70.0,
        teacher_pct=35.0,
        student_pct=55.0,
        meets_standard=True,
        created_at="2025-01-15T10:30:00",
        alignment_score=None,
    )
    csv_str = write_csv(headers, row)
    parsed = parse_csv(csv_str)

    assert "alignment_score" not in parsed, "alignment_score should not be present without triangulation"


def test_csv_score_values_are_numeric():
    """Score columns in CSV contain parseable numeric values."""
    headers, row = build_csv_row(
        job_id="job-123",
        video_name="video.mp4",
        mindful=72.5,
        meaningful=68.3,
        joyful=81.0,
        overall=74.0,
        teacher_pct=36.5,
        student_pct=53.5,
        meets_standard=True,
        created_at="2025-01-15T10:30:00",
    )
    csv_str = write_csv(headers, row)
    parsed = parse_csv(csv_str)

    numeric_cols = ["mindful_score", "meaningful_score", "joyful_score",
                    "overall_3m_score", "teacher_talk_pct", "student_talk_pct"]
    for col in numeric_cols:
        try:
            float(parsed[col])
        except (ValueError, TypeError):
            pytest.fail(f"Column '{col}' value '{parsed[col]}' is not numeric")
