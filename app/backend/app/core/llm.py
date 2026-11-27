"""Model routing + lớp gọi model không phụ thuộc nhà cung cấp.

Mỗi tác vụ đọc cấu hình dạng "provider:model" từ .env, ví dụ
MODEL_CHAT=deepseek:deepseek-chat, MODEL_VISION=gemini:gemini-2.5-flash
hoặc qwen:qwen-vl-max.

Provider: deepseek | qwen | openai (cùng API OpenAI) · anthropic · gemini.
"""
import base64
import json
import re
from collections.abc import Iterator
from enum import Enum
from functools import lru_cache

from .config import settings


class Task(str, Enum):
    CHAT = "chat"                # hỏi đáp, Socratic tutor, lọc đoạn liên quan
    VISION = "vision"            # đọc ảnh viết tay → LaTeX
    GRADING = "grading"          # chấm tự luận 3 bước


class LLMError(RuntimeError):
    pass


def route(task: Task) -> tuple[str, str]:
    spec = {
        Task.CHAT: settings.model_chat,
        Task.VISION: settings.model_vision,
        Task.GRADING: settings.model_grading,
    }[task]
    provider, _, model = spec.partition(":")
    return provider.strip().lower(), model.strip()


# ---------- Client ----------
_OPENAI_COMPAT = {
    "deepseek": (lambda: settings.deepseek_api_key, lambda: settings.deepseek_base_url, "DEEPSEEK_API_KEY"),
    "qwen": (lambda: settings.qwen_api_key, lambda: settings.qwen_base_url, "QWEN_API_KEY"),
    "openai": (lambda: settings.openai_api_key, lambda: None, "OPENAI_API_KEY"),
}


@lru_cache(maxsize=8)
def _openai_client(provider: str):
    from openai import OpenAI

    key_fn, url_fn, env = _OPENAI_COMPAT[provider]
    if not key_fn():
        raise LLMError(f"Chưa đặt {env} trong .env")
    return OpenAI(api_key=key_fn(), base_url=url_fn(), timeout=120, max_retries=2)


def provider_ready(task: Task) -> bool:
    provider, _ = route(task)
    if provider in _OPENAI_COMPAT:
        return bool(_OPENAI_COMPAT[provider][0]())
    if provider == "gemini":
        return bool(settings.gemini_api_key)
    if provider == "anthropic":
        import os

        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    return False


# ---------- Văn bản ----------
def complete(task: Task, system: str, messages: list[dict], *, json_mode: bool = False, max_tokens: int = 4000) -> str:
    """Gọi model cho tác vụ. System prompt luôn tách riêng khỏi tin nhắn học sinh."""
    provider, model = route(task)
    if provider in _OPENAI_COMPAT:
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        resp = _openai_client(provider).chat.completions.create(
            model=model, messages=[{"role": "system", "content": system}, *messages],
            max_tokens=max_tokens, temperature=0.2, **kwargs,
        )
        return resp.choices[0].message.content or ""
    if provider == "anthropic":
        return _anthropic(model, system, messages, max_tokens)
    if provider == "gemini":
        return _gemini_text(model, system, messages, json_mode)
    raise LLMError(f"Provider không hỗ trợ: {provider}")


def stream(task: Task, system: str, messages: list[dict], max_tokens: int = 2500) -> Iterator[str]:
    """Trả từng mẩu văn bản để stream SSE cho học sinh."""
    provider, model = route(task)
    if provider in _OPENAI_COMPAT:
        resp = _openai_client(provider).chat.completions.create(
            model=model, messages=[{"role": "system", "content": system}, *messages],
            max_tokens=max_tokens, temperature=0.3, stream=True,
        )
        for chunk in resp:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
        return
    # Provider chưa stream: trả một lần
    yield complete(task, system, messages, max_tokens=max_tokens)


def parse_json(text: str) -> dict:
    """Đọc JSON từ câu trả lời của model (chịu được ```json … ``` bao quanh)."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise LLMError("Model không trả về JSON")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise LLMError(f"JSON không hợp lệ: {e}") from e


def complete_json(task: Task, system: str, messages: list[dict], max_tokens: int = 4000) -> dict:
    return parse_json(complete(task, system, messages, json_mode=True, max_tokens=max_tokens))


def _anthropic(model: str, system: str, messages: list[dict], max_tokens: int) -> str:
    import anthropic

    resp = anthropic.Anthropic().messages.create(model=model, max_tokens=max_tokens, system=system, messages=messages)
    if resp.stop_reason == "refusal":
        return "Xin lỗi, trợ lý không thể trả lời câu hỏi này."
    return "".join(b.text for b in resp.content if b.type == "text")


def _gemini_client():
    from google import genai

    if not settings.gemini_api_key:
        raise LLMError("Chưa đặt GEMINI_API_KEY trong .env")
    return genai.Client(api_key=settings.gemini_api_key)


def _gemini_text(model: str, system: str, messages: list[dict], json_mode: bool) -> str:
    from google.genai import types

    contents = [types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part(text=m["content"])])
                for m in messages]
    cfg = types.GenerateContentConfig(system_instruction=system,
                                      response_mime_type="application/json" if json_mode else None)
    return _gemini_client().models.generate_content(model=model, contents=contents, config=cfg).text or ""


# ---------- Ảnh (VLM) ----------
def vision_ready() -> bool:
    return provider_ready(Task.VISION)


def read_image(image: bytes, mime: str, system: str, instruction: str) -> str:
    """Gửi ảnh bài làm cho VLM, trả về văn bản (thường là JSON theo instruction)."""
    provider, model = route(Task.VISION)
    if provider == "gemini":
        from google.genai import types

        cfg = types.GenerateContentConfig(system_instruction=system, response_mime_type="application/json")
        resp = _gemini_client().models.generate_content(
            model=model, contents=[types.Part.from_bytes(data=image, mime_type=mime), instruction], config=cfg)
        return resp.text or ""
    if provider in ("qwen", "openai"):
        data_uri = f"data:{mime};base64,{base64.b64encode(image).decode()}"
        resp = _openai_client(provider).chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": [{"type": "image_url", "image_url": {"url": data_uri}},
                                                   {"type": "text", "text": instruction}]}],
            max_tokens=4000, temperature=0,
        )
        return resp.choices[0].message.content or ""
    raise LLMError(f"Provider {provider} không đọc được ảnh. Đặt MODEL_VISION=gemini:… hoặc qwen:…")


# ---------- Embedding (tuỳ chọn) ----------
EMBED_DIM = 1024


def embeddings_enabled() -> bool:
    return settings.embedding_model not in ("", "none")


@lru_cache(maxsize=1)
def _st_model():
    from sentence_transformers import SentenceTransformer  # cài thêm: pip install sentence-transformers

    return SentenceTransformer("BAAI/bge-m3")


def embed(texts: list[str]) -> list[list[float]] | None:
    """Vector 1024 chiều, hoặc None nếu đang dùng tìm theo từ khoá."""
    if not embeddings_enabled() or not texts:
        return None
    name = settings.embedding_model
    if name == "bge-m3":
        return [list(map(float, v)) for v in _st_model().encode(texts, normalize_embeddings=True)]
    if name.startswith("openai:"):
        resp = _openai_client("openai").embeddings.create(model=name.split(":", 1)[1], input=texts, dimensions=EMBED_DIM)
        return [d.embedding for d in resp.data]
    raise LLMError(f"EMBEDDING_MODEL không hỗ trợ: {name}")
