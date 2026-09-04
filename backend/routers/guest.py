"""
Guest Mode Router
Allows unauthenticated users to try prediction with limitations
"""
import os
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.db_models import SystemConfig
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

router = APIRouter(prefix="/guest", tags=["guest"])

# Temporary upload directory for guest files
GUEST_UPLOAD = Path("backend/uploads/guest")
GUEST_UPLOAD.mkdir(parents=True, exist_ok=True)

# In-memory rate limiting (per IP)
# Format: {ip: {"count": int, "reset_time": datetime}}
rate_limit_store: Dict[str, Dict] = {}

# Guest limitations
MAX_PREDICTIONS_PER_SESSION = 5
MAX_FILE_SIZE_MB = 50
RATE_LIMIT_WINDOW_MINUTES = 60


def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def check_rate_limit(ip: str) -> tuple[bool, int]:
    """
    Check if IP has exceeded rate limit
    Returns: (is_allowed, remaining_predictions)
    """
    now = datetime.now()
    
    if ip not in rate_limit_store:
        rate_limit_store[ip] = {
            "count": 0,
            "reset_time": now + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
        }
    
    data = rate_limit_store[ip]
    
    # Reset if window expired
    if now > data["reset_time"]:
        data["count"] = 0
        data["reset_time"] = now + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    
    remaining = MAX_PREDICTIONS_PER_SESSION - data["count"]
    is_allowed = data["count"] < MAX_PREDICTIONS_PER_SESSION
    
    return is_allowed, max(0, remaining)


def increment_rate_limit(ip: str):
    """Increment prediction count for IP"""
    if ip in rate_limit_store:
        rate_limit_store[ip]["count"] += 1





def cleanup_old_guest_files():
    """Clean up guest files older than 1 hour"""
    try:
        now = datetime.now()
        for file_path in GUEST_UPLOAD.glob("*"):
            if file_path.is_file():
                file_age = now - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age > timedelta(hours=1):
                    file_path.unlink()
                    print(f"🗑️ Cleaned up old guest file: {file_path.name}")
    except Exception as e:
        print(f"❌ Error cleaning up guest files: {e}")


@router.get("/limits")
async def get_guest_limits(request: Request):
    """Get guest mode limitations and remaining predictions"""
    ip = get_client_ip(request)
    is_allowed, remaining = check_rate_limit(ip)
    
    return {
        "max_predictions": MAX_PREDICTIONS_PER_SESSION,
        "remaining_predictions": remaining,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "rate_limit_window_minutes": RATE_LIMIT_WINDOW_MINUTES,
        "is_allowed": is_allowed,
    }


@router.post("/predict")
async def guest_predict(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Guest prediction endpoint - no authentication required
    Limitations:
    - Max 5 predictions per hour per IP
    - Max file size: 50MB
    - Results not saved to database
    - Temporary files cleaned up after 1 hour
    """
    # Get client IP
    ip = get_client_ip(request)
    
    # Check rate limit
    is_allowed, remaining = check_rate_limit(ip)
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Batas prediksi guest tercapai. Silakan daftar untuk akses unlimited. Reset dalam {RATE_LIMIT_WINDOW_MINUTES} menit."
        )
    
    filename = file.filename.lower()
    
    # File size validation (50MB max for guests)
    MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File terlalu besar untuk mode guest. Maksimal {MAX_FILE_SIZE_MB}MB. Ukuran file: {file_size / (1024*1024):.1f}MB. Daftar untuk limit 500MB."
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Generate unique filename for guest
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"guest_{unique_id}_{file.filename}"
    
    # Get confidence threshold
    threshold_config = db.query(SystemConfig).filter(SystemConfig.key == "confidence_threshold").first()
    confidence_threshold = float(threshold_config.value) if threshold_config else 70.0
    
    try:
        if filename.endswith(".mp4"):
            # Video prediction
            dest = GUEST_UPLOAD / safe_filename
            with open(dest, "wb") as f:
                f.write(file_content)
            
            raise HTTPException(
                status_code=501, 
                detail="Fitur prediksi video dasar (CNN) telah dinonaktifkan. Silakan gunakan fitur Analisis Video 3M setelah login."
            )
        
        else:
            raise HTTPException(status_code=400, detail="File harus .mp4. Untuk dokumen, gunakan fitur Analisis DLI setelah login.")
        
        # Increment rate limit
        increment_rate_limit(ip)
        
        # Get updated remaining count
        _, remaining_after = check_rate_limit(ip)
        
        # Check if confidence is below threshold
        low_confidence = confidence < confidence_threshold
        
        # Cleanup old files
        cleanup_old_guest_files()
        
        return {
            "file_name": file.filename,
            "file_type": file_type,
            "label": label,
            "confidence": confidence,
            "low_confidence": low_confidence,
            "confidence_threshold": confidence_threshold,
            "guest_mode": True,
            "remaining_predictions": remaining_after,
            "max_predictions": MAX_PREDICTIONS_PER_SESSION,
            "message": "Hasil prediksi tidak disimpan. Daftar untuk menyimpan riwayat prediksi." if remaining_after > 0 else "Batas prediksi guest tercapai. Daftar untuk akses unlimited."
        }
    
    except Exception as e:
        # Clean up file on error
        if 'dest' in locals() and dest.exists():
            dest.unlink()
        raise HTTPException(status_code=500, detail=f"Error saat prediksi: {str(e)}")
