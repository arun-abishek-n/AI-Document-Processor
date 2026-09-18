from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import hash_password, require_role
from app.database import get_db
from app.models import User
from app.schemas_auth import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])

VALID_ROLES = {"admin", "manager", "executive"}


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(require_role("admin"))) -> list[User]:
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate, db: Session = Depends(get_db), _admin: User = Depends(require_role("admin"))
) -> User:
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}.")
    if db.query(User).filter(User.username == payload.username).first() is not None:
        raise HTTPException(status_code=400, detail=f"Username '{payload.username}' is already taken.")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _admin: User = Depends(require_role("admin"))
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.role is not None and payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}.")

    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.commit()
    return user
