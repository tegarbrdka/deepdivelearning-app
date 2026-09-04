from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.db_models import User, ActivityLog
from backend.schemas.schemas import UserRegister, UserLogin, TokenResponse
from backend.services.auth_service import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log = ActivityLog(user_id=user.id, action="register", detail=f"User {user.username} registered")
    db.add(log)
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, role=user.role, username=user.username)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    log = ActivityLog(user_id=user.id, action="login", detail=f"User {user.username} logged in")
    db.add(log)
    db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, role=user.role, username=user.username)


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}


@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }


@router.put("/profile")
def update_profile(
    username: str = None,
    email: str = None,
    current_password: str = None,
    new_password: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Update username
    if username and username != current_user.username:
        existing = db.query(User).filter(User.username == username, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username sudah digunakan")
        current_user.username = username
    
    # Update email
    if email and email != current_user.email:
        existing = db.query(User).filter(User.email == email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email sudah digunakan")
        current_user.email = email
    
    # Update password
    if new_password:
        if not current_password:
            raise HTTPException(status_code=400, detail="Password lama wajib diisi")
        if not verify_password(current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Password lama salah")
        current_user.password_hash = hash_password(new_password)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile berhasil diupdate",
        "username": current_user.username,
        "email": current_user.email
    }

