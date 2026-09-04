# Models package
# Importing all models here ensures Base.metadata is fully populated
# when init_db() calls Base.metadata.create_all().

from backend.models.db_models import (  # noqa: F401
    User,
    Prediction,
    DatasetVideo,
    DatasetDocument,
    TrainingLog,
    ActivityLog,
    SystemConfig,
    # 3M Video Analysis models
    VideoAnalysisJob,
    VideoAnalysisResult,
    VideoFragment3M,
    EvidenceClip3M,
    LessonPlan3M,
    TriangulationResult3M,
)

from backend.models.ground_truth_models import (  # noqa: F401
    GroundTruthAnnotation,
    EvaluationReport,
)
