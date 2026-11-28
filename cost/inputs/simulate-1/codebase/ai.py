"""Nối model — chỗ DUY NHẤT trong bản chạy thử gọi model AI. Owner: Ninh (ticket N-04).

Hợp đồng (giữ nguyên để khung đo được token):
    call_model(system: str, user: str) -> dict với 4 khoá
        "text":       str   chữ model trả về
        "model":      str   tên model đã gọi (để tra giá ở bảng giá model)
        "tokens_in":  int   số token vào, lấy từ trường usage trong phản hồi API — KHÔNG ước lượng
        "tokens_out": int   số token ra, gồm cả token suy luận / suy nghĩ nếu API tính riêng
    @model_call (từ tracing.py) tự ghi mỗi lần gọi vào trace; agent.py gọi call_model bao nhiêu lần
    cũng được, khung tự cộng token.
    Lỗi gọi model (hết lượt, sai key, mất mạng): cứ để exception bay ra — khung ghi lỗi vào cột error.

Chế độ giả (mặc định khi .env chưa có MODEL_PROVIDER, hoặc MODEL_PROVIDER=fake):
    trả một câu giả cố định, model "fake", token 0 — để luồng chạy hết từ trước CP2 (guide bước 3.2).
    Lượt `run.py eval` / `run.py simulate` chạy bằng model giả KHÔNG được tính.

Nối model thật (docs/connect-model.md) — điền .env (chép từ .env.example), KHÔNG dán key vào file này:
    MODEL_PROVIDER=deepseek   MODEL_NAME=deepseek-chat      API_KEY=<key DeepSeek>   (giống app: MODEL_CHAT)
    MODEL_PROVIDER=gemini     MODEL_NAME=gemini-2.5-flash   API_KEY=<key Google AI Studio>
    MODEL_PROVIDER=openai     MODEL_NAME=<mã model OpenAI>  API_KEY=<key OpenAI>
    Tuỳ chọn: MODEL_BASE_URL (đổi địa chỉ API, vd proxy), MODEL_TEMPERATURE (mặc định 0.2 cho lượt eval ổn định),
    MODEL_MAX_TOKENS (mặc định 1024), MODEL_TIMEOUT (giây, mặc định 60).
    Chỉ dùng thư viện chuẩn (urllib), không cần pip install.
"""
import json
import os
import time
import urllib.error
import urllib.request

from tracing import model_call

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path=os.path.join(ROOT, ".env")):
    """Đọc file .env (KEY=VALUE mỗi dòng) vào biến môi trường, không ghi đè biến đã có. Khung — không cần sửa."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
MODEL_PROVIDER = (os.environ.get("MODEL_PROVIDER") or "fake").strip().lower()
MODEL_NAME = (os.environ.get("MODEL_NAME") or "").strip()
API_KEY = (os.environ.get("API_KEY") or "").strip()

DEFAULT_MODEL = {"deepseek": "deepseek-chat", "gemini": "gemini-2.5-flash"}  # khi .env để trống MODEL_NAME
MODEL_NAME = MODEL_NAME or DEFAULT_MODEL.get(MODEL_PROVIDER, "")
BASE_URL = {"deepseek": "https://api.deepseek.com", "openai": "https://api.openai.com/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1beta"}
BASE_URL_OVERRIDE = (os.environ.get("MODEL_BASE_URL") or "").strip().rstrip("/")
TEMPERATURE = float(os.environ.get("MODEL_TEMPERATURE") or 0.2)
MAX_TOKENS = int(os.environ.get("MODEL_MAX_TOKENS") or 1024)
TIMEOUT = float(os.environ.get("MODEL_TIMEOUT") or 60)
RETRIES = 2            # thử lại khi 429 / 5xx / mất mạng thoáng qua (chờ 2s, 4s); lỗi 4xx khác bay ra ngay
SHOW_RAW = False       # đổi thành True để in nguyên phản hồi của API khi cần tìm tên trường


def post_json(url, headers, body, timeout=TIMEOUT):
    """Gửi POST JSON, trả về JSON phản hồi. Chỉ dùng thư viện chuẩn (urllib). Lỗi không in key."""
    data = json.dumps(body).encode("utf-8")
    for attempt in range(RETRIES + 1):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers=dict({"Content-Type": "application/json"}, **headers))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if (e.code == 429 or e.code >= 500) and attempt < RETRIES:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError("HTTP %d từ %s: %s" % (e.code, MODEL_PROVIDER, detail)) from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < RETRIES:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError("Không gọi được %s: %s" % (MODEL_PROVIDER, getattr(e, "reason", e))) from None
    if SHOW_RAW:
        print(json.dumps(out, ensure_ascii=False, indent=2)[:3000])
    return out


def _base(provider):
    return BASE_URL_OVERRIDE or BASE_URL[provider]


def call_openai_compatible(system, user, provider):
    """DeepSeek / OpenAI (cùng định dạng Chat Completions). Token từ usage.prompt_tokens / completion_tokens;
    với deepseek-reasoner, completion_tokens đã gồm token suy luận (reasoning_tokens) nên không cộng thêm."""
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    reasoning_model = MODEL_NAME.startswith(("deepseek-reasoner", "o1", "o3", "o4", "gpt-5", "gpt-6"))
    limit_key = "max_completion_tokens" if provider == "openai" and reasoning_model else "max_tokens"
    body = {"model": MODEL_NAME, "messages": messages, limit_key: MAX_TOKENS, "stream": False}
    if not reasoning_model:
        body["temperature"] = TEMPERATURE  # các model suy luận không nhận temperature
    data = post_json(_base(provider) + "/chat/completions", {"Authorization": "Bearer " + API_KEY}, body)
    u = data["usage"]
    return {"text": data["choices"][0]["message"].get("content") or "",
            "tokens_in": u["prompt_tokens"], "tokens_out": u["completion_tokens"]}


def call_gemini(system, user):
    """Gemini REST generateContent. Token từ usageMetadata: vào = promptTokenCount,
    ra = candidatesTokenCount + thoughtsTokenCount (token suy nghĩ của model 2.5 tính tiền riêng, phải cộng vào)."""
    body = {"contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": TEMPERATURE, "maxOutputTokens": MAX_TOKENS}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    data = post_json("%s/models/%s:generateContent" % (_base("gemini"), MODEL_NAME), {"x-goog-api-key": API_KEY}, body)
    cands = data.get("candidates") or []
    if not cands:
        raise RuntimeError("Gemini không trả câu nào: %s" % json.dumps(data.get("promptFeedback", data))[:300])
    parts = (cands[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    u = data.get("usageMetadata") or {}
    if "promptTokenCount" not in u:
        raise RuntimeError("Gemini không trả usageMetadata — không được ước lượng token (bật SHOW_RAW để xem)")
    return {"text": text, "tokens_in": u["promptTokenCount"],
            "tokens_out": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)}


@model_call
def call_model(system: str, user: str) -> dict:
    if MODEL_PROVIDER == "fake":              # nhánh fake của khung — giữ nguyên 3 dòng này
        last = (user.strip().splitlines() or [""])[-1]
        return {"text": "[câu trả lời giả — chưa nối model] " + last[:60], "model": "fake", "tokens_in": 0, "tokens_out": 0}
    if not API_KEY:
        raise RuntimeError("Chưa có API_KEY trong .env cho MODEL_PROVIDER=%s (xem docs/connect-model.md)" % MODEL_PROVIDER)
    if MODEL_PROVIDER in ("deepseek", "openai"):
        r = call_openai_compatible(system, user, MODEL_PROVIDER)
    elif MODEL_PROVIDER == "gemini":
        r = call_gemini(system, user)
    else:
        raise NotImplementedError("MODEL_PROVIDER=%s chưa hỗ trợ — dùng deepseek / gemini / openai, "
                                  "hoặc thêm nhánh theo docs/connect-model.md" % MODEL_PROVIDER)
    return {"text": r["text"], "model": MODEL_NAME,
            "tokens_in": int(r["tokens_in"]), "tokens_out": int(r["tokens_out"])}
