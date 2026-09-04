from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Prediction ────────────────────────────────────────────────────────────────
class PredictionOut(BaseModel):
    id: int
    file_type: str
    file_name: Optional[str]
    label: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dataset ───────────────────────────────────────────────────────────────────
class DatasetVideoOut(BaseModel):
    id: int
    file_name: Optional[str]
    label: str
    group_name: Optional[str] = "Default"
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetDocumentOut(BaseModel):
    id: int
    file_name: Optional[str]
    label: str
    group_name: Optional[str] = "Default"
    created_at: datetime

    class Config:
        from_attributes = True


# ── Training ──────────────────────────────────────────────────────────────────
class TrainBERTRequest(BaseModel):
    epochs: int = 5
    learning_rate: float = 2e-5
    batch_size: int = 4  # Reduced from 8 for small datasets
    early_stopping_patience: int = 5
    use_lr_scheduler: bool = True


class TrainingStatusOut(BaseModel):
    job_id: str
    status: str  # "running" | "completed" | "failed"
    progress: float
    current_epoch: int
    total_epochs: int
    logs: List[dict]


# ── Model Versions ────────────────────────────────────────────────────────────
class ModelVersionOut(BaseModel):
    id: int
    version: str
    accuracy: Optional[float]
    f1_score: Optional[float]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Admin ─────────────────────────────────────────────────────────────────────
class AdminStats(BaseModel):
    total_predictions: int
    total_users: int
    total_video_dataset: int
    total_document_dataset: int


class ActivityLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    detail: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SystemConfigUpdate(BaseModel):
    key: str
    value: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"


class UserUpdate(BaseModel):
    role: Optional[str]
    password: Optional[str]
