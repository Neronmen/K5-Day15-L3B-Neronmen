"""Auth & RBAC: mọi API kiểm tra token và quyền sở hữu."""
import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

bearer = HTTPBearer(auto_error=False)
_ITER = 390_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITER)
    return f"pbkdf2_sha256${_ITER}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        _, iters, salt, dk = stored.split("$")
        new = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iters))
        return hmac.compare_digest(new, base64.b64decode(dk))
    except ValueError:
        return False


def create_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": user_id, "role": role, "iat": now, "exp": now + timedelta(minutes=settings.jwt_expire_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@dataclass
class CurrentUser:
    id: str
    role: str  # teacher | student


def get_current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> CurrentUser:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa đăng nhập")
    try:
        data = jwt.decode(cred.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập đã hết hạn")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token không hợp lệ")
    return CurrentUser(id=data["sub"], role=data["role"])


def require_teacher(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ giáo viên")
    return user


def require_student(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ học sinh")
    return user


def assert_class_owner(user: CurrentUser, class_teacher_id: str) -> None:
    """vd POST /classes/{id}/students: role == teacher và teacher_id == class.owner."""
    if user.role != "teacher" or user.id != class_teacher_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không sở hữu lớp này")


def assert_enrolled(is_enrolled: bool) -> None:
    if not is_enrolled:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không thuộc lớp này")
 