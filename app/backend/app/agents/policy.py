"""Rule 3: chế độ Sư phạm. Luôn tính bằng giờ server."""
from datetime import datetime, timezone
from typing import Literal

TutorMode = Literal["hint", "answer"]


def get_tutor_mode(role: str, due_at: datetime, now: datetime | None = None) -> TutorMode:
    now = now or datetime.now(timezone.utc)
    if role != "student":
        return "answer"  # giáo viên luôn xem được lời giải
    return "answer" if now >= due_at else "hint"
