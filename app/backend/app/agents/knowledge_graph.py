"""Knowledge Agent (LangGraph): retrieve → relevance grader → quyết định nhánh.

Phần sinh câu trả lời được stream riêng (SSE) sau khi graph chọn xong nhánh:
- "answer": có đoạn tài liệu liên quan → trả lời kèm [Nguồn: …]
- "extended": không có đoạn nào, lớp ở chế độ mở rộng → được dùng kiến thức ngoài có nhãn ⚠️
- "no_source": không có đoạn nào, lớp khoá cứng → trả lời cố định, không gọi model sinh văn bản
"""
import json
import logging
from typing import TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.core import llm
from app.core.tenancy import TenantScope, search_chunks

from .prompts import RELEVANCE_GRADER

log = logging.getLogger(__name__)


class KState(TypedDict, total=False):
    question: str
    search_query: str
    scope: TenantScope
    document_id: str | None
    ai_mode: str                 # strict | extended
    chunks: list[dict]           # {document_id, page_number, source_label, text}
    relevant: list[dict]
    route: str                   # answer | extended | no_source


def _chunk_dict(c) -> dict:
    return {"document_id": c.document_id, "page_number": c.page_number, "source_label": c.source_label, "text": c.text}


def make_retrieve(db: Session):
    def retrieve(state: KState) -> KState:
        """Lấy đoạn bài giảng qua tenancy.search_chunks (luôn lọc theo lớp, Rule 2)."""
        q = state.get("search_query") or state["question"]
        found = search_chunks(db, state["scope"], q, k=8)
        # Ưu tiên đoạn của tài liệu đang mở nhưng vẫn cho phép đoạn từ tài liệu khác cùng lớp
        doc_id = state.get("document_id")
        if doc_id:
            found.sort(key=lambda c: c.document_id != doc_id)
        return {"chunks": [_chunk_dict(c) for c in found]}
    return retrieve


def grade_relevance(state: KState) -> KState:
    """Relevance Grader: một lần gọi model nhỏ để chọn các đoạn thực sự giúp trả lời câu hỏi."""
    chunks = state.get("chunks") or []
    if not chunks:
        return {"relevant": []}
    numbered = "\n\n".join(f"[{i}] ({c['source_label']})\n{c['text'][:900]}" for i, c in enumerate(chunks))
    user = f"<cau_hoi>\n{state['question']}\n</cau_hoi>\n\n<cac_doan>\n{numbered}\n</cac_doan>"
    try:
        out = llm.complete_json(llm.Task.CHAT, RELEVANCE_GRADER, [{"role": "user", "content": user}], max_tokens=300)
        idx = [int(i) for i in out.get("relevant", []) if str(i).lstrip("-").isdigit()]
        keep = [chunks[i] for i in idx if 0 <= i < len(chunks)]
    except Exception as e:  # noqa: BLE001 - lỗi bộ lọc: giữ 4 đoạn điểm cao nhất thay vì chặn học sinh
        log.warning("relevance grader lỗi: %s", e)
        keep = chunks[:4]
    return {"relevant": keep[:6]}


def decide(state: KState) -> KState:
    if state.get("relevant"):
        return {"route": "answer"}
    # Lớp khoá cứng: không có nguồn thì dừng, không để model tự bịa
    return {"route": "extended" if state.get("ai_mode") == "extended" else "no_source"}


def build_graph(db: Session):
    g = StateGraph(KState)
    g.add_node("retrieve", make_retrieve(db))
    g.add_node("grade_relevance", grade_relevance)
    g.add_node("decide", decide)
    g.set_entry_point("retrieve")
    g.add_edge("retrieve", "grade_relevance")
    g.add_edge("grade_relevance", "decide")
    g.add_edge("decide", END)
    return g.compile()


def run(db: Session, *, question: str, scope: TenantScope, ai_mode: str,
        document_id: str | None = None, search_query: str | None = None) -> KState:
    return build_graph(db).invoke({
        "question": question, "search_query": search_query or question, "scope": scope,
        "ai_mode": ai_mode, "document_id": document_id,
    })


def debug_dump(state: KState) -> str:
    return json.dumps({k: v for k, v in state.items() if k != "scope"}, ensure_ascii=False)[:2000]
