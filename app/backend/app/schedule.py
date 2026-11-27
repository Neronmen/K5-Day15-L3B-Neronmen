"""Lịch học: buổi lặp hằng tuần + báo nghỉ / học bù từ thông báo. Mọi giờ theo giờ Việt Nam (UTC+7)."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Announcement, AnnouncementKind, ClassSession, Classroom
from app.schemas import AnnouncementOut, CalendarItem, SessionOut

VN_TZ = timezone(timedelta(hours=7))
WEEKDAY_SHORT = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
MAX_DAYS = 62


def today_vn() -> date:
    return datetime.now(VN_TZ).date()


def at_vn(d: date, hhmm: str) -> datetime:
    h, m = map(int, hhmm.split(":"))
    return datetime(d.year, d.month, d.day, h, m, tzinfo=VN_TZ)


def session_out(s: ClassSession) -> SessionOut:
    return SessionOut(id=s.id, weekday=s.weekday, start_time=s.start_time, end_time=s.end_time, room=s.room)


def announcement_out(a: Announcement, class_name: str) -> AnnouncementOut:
    from app.routers.common import aware

    return AnnouncementOut(
        id=a.id, class_id=a.class_id, class_name=class_name, kind=a.kind, title=a.title, body=a.body or "",
        event_date=a.event_date, event_start=a.event_start, event_end=a.event_end, session_id=a.session_id,
        pinned=a.pinned, created_at=aware(a.created_at),
    )


def class_sessions(db: Session, class_id: str) -> list[ClassSession]:
    return list(db.scalars(select(ClassSession).where(ClassSession.class_id == class_id)
                           .order_by(ClassSession.weekday, ClassSession.start_time)))


def schedule_text(sessions: list[ClassSession]) -> str:
    return " · ".join(f"{WEEKDAY_SHORT[s.weekday]} {s.start_time}–{s.end_time}" for s in sessions)


def calendar(db: Session, classes: list[Classroom], start: date, days: int) -> list[CalendarItem]:
    """Các buổi học trong [start, start+days): buổi thường (đánh dấu nghỉ nếu có báo nghỉ) + buổi học bù."""
    days = max(1, min(days, MAX_DAYS))
    if not classes:
        return []
    by_id = {c.id: c for c in classes}
    end = start + timedelta(days=days)
    sessions = list(db.scalars(select(ClassSession).where(ClassSession.class_id.in_(by_id))))
    events = list(db.scalars(select(Announcement).where(
        Announcement.class_id.in_(by_id),
        Announcement.kind.in_([AnnouncementKind.CANCEL.value, AnnouncementKind.MAKEUP.value]),
        Announcement.event_date >= start, Announcement.event_date < end,
    ).order_by(Announcement.created_at)))
    cancels: dict[tuple[str, date], list[Announcement]] = defaultdict(list)
    for e in events:
        if e.kind == AnnouncementKind.CANCEL.value:
            cancels[(e.class_id, e.event_date)].append(e)

    by_weekday: dict[int, list[ClassSession]] = defaultdict(list)
    for s in sessions:
        by_weekday[s.weekday].append(s)

    items: list[CalendarItem] = []
    for i in range(days):
        d = start + timedelta(days=i)
        for s in by_weekday.get(d.weekday(), []):
            c = by_id[s.class_id]
            hit = next((e for e in cancels.get((c.id, d), []) if e.session_id in (None, s.id)), None)
            items.append(CalendarItem(
                date=d, start_time=s.start_time, end_time=s.end_time, class_id=c.id, class_name=c.name,
                subject=c.subject_id, room=s.room, kind="regular", session_id=s.id,
                cancelled=hit is not None, note=hit.title if hit else None,
            ))
    for e in events:
        if e.kind == AnnouncementKind.MAKEUP.value and e.event_start and e.event_end:
            c = by_id[e.class_id]
            items.append(CalendarItem(
                date=e.event_date, start_time=e.event_start, end_time=e.event_end, class_id=c.id, class_name=c.name,
                subject=c.subject_id, room=None, kind="makeup", session_id=None, note=e.title,
            ))
    items.sort(key=lambda x: (x.date, x.start_time, x.class_name))
    return items


def next_sessions(db: Session, classes: list[Classroom]) -> dict[str, datetime]:
    """Giờ bắt đầu buổi học sắp tới (chưa kết thúc, không bị nghỉ) của từng lớp, tìm trong 3 tuần."""
    now = datetime.now(VN_TZ)
    out: dict[str, datetime] = {}
    for it in calendar(db, classes, now.date(), 21):
        if it.cancelled or it.class_id in out or at_vn(it.date, it.end_time) <= now:
            continue
        out[it.class_id] = at_vn(it.date, it.start_time)
    return out
