from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(16), default="user")  # "user" | "admin"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    predictions = relationship("Prediction", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(String(16), nullable=False)  # "video" | "document"
    file_path = Column(String(512))
    file_name = Column(String(256))
    label = Column(String(64))
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # DLI fields (nullable for backward compatibility)
    dli_score = Column(Float, nullable=True)
    dli_category = Column(String(64), nullable=True)
    mindful_score = Column(Float, nullable=True)
    meaningful_score = Column(Float, nullable=True)
    joyful_score = Column(Float, nullable=True)
    pedagogis_score = Column(Float, nullable=True)
    digital_score = Column(Float, nullable=True)
    dli_data = Column(JSON, nullable=True)  # Store full DLI result as JSON

    user = relationship("User", back_populates="predictions")
    
    def is_dli_analysis(self) -> bool:
        """Check if this prediction includes DLI analysis"""
        return self.dli_score is not None
    
    def get_dli_scores(self) -> dict:
        """Get all DLI aspect scores as a dictionary"""
        if not self.is_dli_analysis():
            return None
        
        return {
            'mindful': self.mindful_score,
            'meaningful': self.meaningful_score,
            'joyful': self.joyful_score,
            'pedagogis': self.pedagogis_score,
            'digital': self.digital_score
        }
    
    def set_dli_data(self, dli_result: dict):
        """
        Set DLI data from analysis result
        
        Args:
            dli_result: Dictionary containing DLI analysis results with keys:
                - dli_score: Overall DLI score (0-100)
                - dli_category: Category (Siap Implementasi, Perlu Perbaikan, etc.)
                - scores: Dict with aspect scores (mindful, meaningful, joyful, pedagogis, digital)
                - Full DLI data stored in dli_data JSON field
        """
        self.dli_score = dli_result.get('dli_score')
        self.dli_category = dli_result.get('dli_category')
        
        scores = dli_result.get('scores', {})
        self.mindful_score = scores.get('mindful')
        self.meaningful_score = scores.get('meaningful')
        self.joyful_score = scores.get('joyful')
        self.pedagogis_score = scores.get('pedagogis')
        self.digital_score = scores.get('digital')
        
        # Store complete DLI data as JSON
        import json
        self.dli_data = json.dumps(dli_result) if dli_result else None
    
    def get_full_dli_data(self) -> dict:
        """Get complete DLI analysis data from JSON field"""
        if not self.dli_data:
            return None
        
        import json
        return json.loads(self.dli_data) if isinstance(self.dli_data, str) else self.dli_data


class DatasetVideo(Base):
    __tablename__ = "dataset_video"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(256))
    label = Column(String(64), nullable=False)  # "Deep Learning" | "Bukan Deep Learning"
    group_name = Column(String(128), default="Default")  # Group/tag for organization
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DatasetDocument(Base):
    __tablename__ = "dataset_document"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(256))
    label = Column(String(64), nullable=False)  # "Baik" | "Cukup" | "Kurang"
    group_name = Column(String(128), default="Default")  # Group/tag for organization
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())





class TrainingLog(Base):
    __tablename__ = "training_logs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), index=True)
    model_type = Column(String(16))  # "cnn"
    epoch = Column(Integer)
    loss = Column(Float)
    accuracy = Column(Float)
    val_loss = Column(Float)
    val_accuracy = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(64))
    detail = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")


class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# 3M Video Analysis models
# ---------------------------------------------------------------------------

class VideoAnalysisJob(Base):
    __tablename__ = "video_analysis_jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_path = Column(String(512), nullable=False)
    video_name = Column(String(256))
    rpp_path = Column(String(512), nullable=True)
    status = Column(String(32), default="queued")
    stage = Column(String(64), nullable=True)
    progress = Column(Float, default=0.0)
    error_msg = Column(Text, nullable=True)
    video_duration_sec = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    user = relationship("User")
    result = relationship("VideoAnalysisResult", back_populates="job", uselist=False)
    fragments = relationship("VideoFragment3M", back_populates="job")


class VideoAnalysisResult(Base):
    __tablename__ = "video_analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("video_analysis_jobs.job_id"), unique=True)
    mindful_score = Column(Float, nullable=True)
    meaningful_score = Column(Float, nullable=True)
    joyful_score = Column(Float, nullable=True)
    overall_3m_score = Column(Float, nullable=True)
    gaze_score = Column(Float, nullable=True)
    posture_score = Column(Float, nullable=True)
    silence_quality_score = Column(Float, nullable=True)
    seating_score = Column(Float, nullable=True)
    talk_time_score = Column(Float, nullable=True)
    question_type_score = Column(Float, nullable=True)
    teacher_movement_score = Column(Float, nullable=True)
    expression_score = Column(Float, nullable=True)
    acoustic_score = Column(Float, nullable=True)
    collaboration_score = Column(Float, nullable=True)
    risk_taking_score = Column(Float, nullable=True)
    teacher_talk_pct = Column(Float, nullable=True)
    student_talk_pct = Column(Float, nullable=True)
    silence_pct = Column(Float, nullable=True)
    meets_dl_standard = Column(Boolean, nullable=True)
    timeline_data = Column(JSON, nullable=True)
    heatmap_data = Column(JSON, nullable=True)
    aha_moments = Column(JSON, nullable=True)
    laughter_events = Column(JSON, nullable=True)
    applause_events = Column(JSON, nullable=True)
    seating_transitions = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    discussion_groups_count = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    job = relationship("VideoAnalysisJob", back_populates="result")
    evidence_clips = relationship("EvidenceClip3M", back_populates="result")
    triangulation = relationship("TriangulationResult3M", back_populates="result", uselist=False)


class VideoFragment3M(Base):
    __tablename__ = "video_fragments"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("video_analysis_jobs.job_id"), index=True)
    fragment_index = Column(Integer)
    start_sec = Column(Float)
    end_sec = Column(Float)
    mindful_score = Column(Float, nullable=True)
    meaningful_score = Column(Float, nullable=True)
    joyful_score = Column(Float, nullable=True)
    gaze_score = Column(Float, nullable=True)
    posture_score = Column(Float, nullable=True)
    silence_quality_score = Column(Float, nullable=True)
    seating_score = Column(Float, nullable=True)
    talk_time_score = Column(Float, nullable=True)
    question_type_score = Column(Float, nullable=True)
    teacher_movement_score = Column(Float, nullable=True)
    expression_score = Column(Float, nullable=True)
    acoustic_score = Column(Float, nullable=True)
    collaboration_score = Column(Float, nullable=True)
    seating_formation = Column(String(64), nullable=True)
    active_zone_ratio = Column(Float, nullable=True)
    teacher_talk_pct = Column(Float, nullable=True)
    student_talk_pct = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    job = relationship("VideoAnalysisJob", back_populates="fragments")


class EvidenceClip3M(Base):
    __tablename__ = "evidence_clips"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("video_analysis_jobs.job_id"), index=True)
    result_id = Column(Integer, ForeignKey("video_analysis_results.id"))
    clip_path = Column(String(512))
    clip_name = Column(String(256))
    start_sec = Column(Float)
    end_sec = Column(Float)
    clip_type = Column(String(32))
    aspect = Column(String(32))
    description = Column(Text)
    score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    result = relationship("VideoAnalysisResult", back_populates="evidence_clips")


class LessonPlan3M(Base):
    __tablename__ = "lesson_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(256))
    parsed_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User")


class TriangulationResult3M(Base):
    __tablename__ = "triangulation_results"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("video_analysis_jobs.job_id"), unique=True)
    result_id = Column(Integer, ForeignKey("video_analysis_results.id"), unique=True)
    items = Column(JSON, nullable=True)
    alignment_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    result = relationship("VideoAnalysisResult", back_populates="triangulation")
