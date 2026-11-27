from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import CurrentUser, create_token, get_current_user, hash_password, verify_password
from app.db import get_db
from app.models import User
from app.schemas import GoogleLoginIn, LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["đăng nhập"])


def _out(u: User) -> UserOut:
    return UserOut(id=u.id, email=u.email, name=u.name, role=u.role)


def _token(u: User) -> TokenOut:
    return TokenOut(access_token=create_token(u.id, u.role), user=_out(u))


def _new_user(db: Session, *, email: str, name: str, role: str, password_hash: str | None = None,
              google_sub: str | None = None) -> User:
    u = User(email=email, name=name, role=role, password_hash=password_hash, google_sub=google_sub)
    db.add(u)
    db.flush()
    if u.role == "teacher" and settings.demo_class_on_signup:
        from app.onboarding import create_demo_class

        create_demo_class(db, u.id)
    return u


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    u = db.scalar(select(User).where(User.email == email))
    if u and (u.password_hash or u.google_sub):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã có tài khoản")
    if u:
        # Học sinh được giáo viên mời trước: kích hoạt tài khoản, giữ nguyên các lớp đã được thêm
        if body.role != "student":
            raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã được mời với vai trò học sinh")
        u.password_hash = hash_password(body.password)
        u.name = body.name
    else:
        u = _new_user(db, email=email, name=body.name, role=body.role, password_hash=hash_password(body.password))
    db.commit()
    return _token(u)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == body.email.lower()))
    if not u or not verify_password(body.password, u.password_hash):
        detail = "Tài khoản này đăng nhập bằng Google" if u and u.google_sub and not u.password_hash else "Sai email hoặc mật khẩu"
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail)
    return _token(u)


def verify_google_token(credential: str) -> dict:
    """Kiểm chữ ký + audience của ID token Google. Tách riêng để test giả lập được."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    return id_token.verify_oauth2_token(credential, google_requests.Request(), settings.google_client_id)


@router.get("/config")
def auth_config():
    """Frontend hỏi xem có bật đăng nhập Google không."""
    return {"google_client_id": settings.google_client_id or None}


@router.post("/google", response_model=TokenOut)
def google_login(body: GoogleLoginIn, db: Session = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Chưa bật đăng nhập Google (thiếu GOOGLE_CLIENT_ID)")
    try:
        info = verify_google_token(body.credential)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập Google không hợp lệ, thử lại")
    if not info.get("email") or not info.get("email_verified"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email Google chưa được xác minh")
    email, sub = info["email"].lower(), info["sub"]
    name = info.get("name") or email.split("@")[0]

    u = db.scalar(select(User).where(or_(User.google_sub == sub, User.email == email)))
    if u is None:
        if body.role is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chưa có tài khoản với Google này. Vào trang Đăng ký, chọn vai trò rồi bấm Google.")
        u = _new_user(db, email=email, name=name, role=body.role, google_sub=sub)
    else:
        if u.google_sub and u.google_sub != sub:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã liên kết với tài khoản Google khác")
        if not (u.password_hash or u.google_sub) and body.role == "teacher":
            raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã được mời với vai trò học sinh")
        if not u.google_sub:
            u.google_sub = sub  # liên kết: tài khoản mật khẩu hoặc học sinh được mời trước
        if not u.password_hash and (not u.name or u.name == email.split("@")[0]):
            u.name = name
    db.commit()
    return _token(u)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.get(User, user.id)
    if not u:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không còn tồn tại")
    return _out(u)
