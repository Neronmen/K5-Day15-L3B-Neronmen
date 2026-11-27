"""Rule 2: mọi truy vấn đoạn bài giảng phải lọc theo teacher_id, class_id, subject_id.

Đây là cửa duy nhất để truy vấn bảng lecture_chunks. Không gọi thẳng SQL ở chỗ khác.
Có 2 cách tìm:
- Vector (pgvector) khi EMBEDDING_MODEL được cấu hình và DB là PostgreSQL.
- BM25 theo từ khoá (mặc định): không cần embedding, chạy được trên mọi DB.
"""
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import llm
from app.models import LectureChunk


@dataclass(frozen=True)
class TenantScope:
    teacher_id: str
    class_id: str
    subject_id: str

    def __post_init__(self) -> None:
        if not (self.teacher_id and self.class_id and self.subject_id):
            raise ValueError("Thiếu bộ lọc tenant: teacher_id, class_id, subject_id đều bắt buộc")


def _scoped(scope: TenantScope):
    return select(LectureChunk).where(
        LectureChunk.teacher_id == scope.teacher_id,
        LectureChunk.class_id == scope.class_id,
        LectureChunk.subject_id == scope.subject_id,
    )


# Từ hư trong câu hỏi tiếng Việt (đã bỏ dấu) — bỏ qua khi chấm điểm BM25
_STOP = set("""la gi cua va cac nhung mot cho voi thi ma o tai trong ve nay do khi nao sao the nhu bao nhieu
duoc co khong em anh chi minh ban hay giup xin a oi a, vay roi nhe a. the nao lam""".split())


def tokenize(text: str) -> list[str]:
    """Bỏ dấu tiếng Việt để câu hỏi gõ không dấu vẫn khớp bài giảng có dấu."""
    t = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in _STOP]


def _bm25(query: str, chunks: list[LectureChunk], k: int) -> list[LectureChunk]:
    q = tokenize(query)
    if not q or not chunks:
        return []
    docs = [tokenize(c.text) for c in chunks]
    # bigram giúp khớp cụm như "ham hop", "dao ham"
    q_terms = q + [f"{a}_{b}" for a, b in zip(q, q[1:])]
    docs = [d + [f"{a}_{b}" for a, b in zip(d, d[1:])] for d in docs]
    n = len(docs)
    avgdl = sum(len(d) for d in docs) / n or 1
    df = Counter(t for d in docs for t in set(d))
    scored = []
    for c, d in zip(chunks, docs):
        tf = Counter(d)
        s = 0.0
        for t in set(q_terms):
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * len(d) / avgdl))
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:k]]


def search_chunks(db: Session, scope: TenantScope, query: str, k: int = 8,
                  document_id: str | None = None) -> list[LectureChunk]:
    stmt = _scoped(scope)
    if document_id:
        stmt = stmt.where(LectureChunk.document_id == document_id)
    if llm.embeddings_enabled() and db.bind.dialect.name == "postgresql":
        vec = llm.embed([query])[0]
        stmt = stmt.where(LectureChunk.embedding.is_not(None)).order_by(LectureChunk.embedding.cosine_distance(vec)).limit(k)
        return list(db.scalars(stmt))
    return _bm25(query, list(db.scalars(stmt.limit(5000))), k)


def scoped_chunks(db: Session, scope: TenantScope, limit: int = 5000) -> list[LectureChunk]:
    """Mọi đoạn bài giảng của ĐÚNG một lớp (lọc đủ 3 khoá tenant). Lõi codebase/ tự chấm điểm BM25 trên danh sách này
    (agents/core_bridge.py, ticket N-08), nên app không có bản tìm kiếm thứ hai cho khung bài tập."""
    return list(db.scalars(_scoped(scope).limit(limit)))


def search_teacher_chunks(db: Session, teacher_id: str, class_ids: list[str], query: str, k: int = 12,
                          document_ids: list[str] | None = None) -> list[LectureChunk]:
    """Tìm trong tài liệu của NHIỀU lớp cùng một giáo viên (Trợ lý AI giáo viên).

    Luôn lọc cứng teacher_id; class_ids phải là lớp giáo viên này sở hữu (router đã kiểm tra).
    """
    if not teacher_id or not class_ids:
        return []
    stmt = select(LectureChunk).where(LectureChunk.teacher_id == teacher_id, LectureChunk.class_id.in_(class_ids))
    if document_ids:
        stmt = stmt.where(LectureChunk.document_id.in_(document_ids))
    if llm.embeddings_enabled() and db.bind.dialect.name == "postgresql":
        vec = llm.embed([query])[0]
        stmt = stmt.where(LectureChunk.embedding.is_not(None)).order_by(LectureChunk.embedding.cosine_distance(vec)).limit(k)
        return list(db.scalars(stmt))
    return _bm25(query, list(db.scalars(stmt.limit(20000))), k)
