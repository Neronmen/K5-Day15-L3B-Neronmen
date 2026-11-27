"""Xử lý ảnh bài làm: đo độ nét (báo chụp lại ngay khi mờ) và nén trước khi gửi VLM (tiết kiệm token)."""
import io

from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

from app.core.config import settings


def _open(data: bytes) -> Image.Image | None:
    try:
        img = Image.open(io.BytesIO(data))
        return ImageOps.exif_transpose(img)
    except (UnidentifiedImageError, OSError):
        return None  # vd HEIC chưa có plugin: bỏ qua kiểm tra, không chặn học sinh


def sharpness(data: bytes) -> float | None:
    """Phương sai ảnh cạnh (xấp xỉ Laplacian). Ảnh chữ viết rõ cho giá trị cao, ảnh nhoè cho giá trị thấp."""
    img = _open(data)
    if img is None:
        return None
    g = img.convert("L")
    g.thumbnail((1000, 1000))
    lap = g.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
    w, h = lap.size
    if w > 8 and h > 8:
        lap = lap.crop((4, 4, w - 4, h - 4))  # bỏ viền: bộ lọc tạo cạnh giả ở mép ảnh
    return float(ImageStat.Stat(lap).var[0])


def is_blurry(data: bytes) -> bool:
    s = sharpness(data)
    return s is not None and s < settings.blur_threshold


def compress_for_vision(data: bytes, mime: str) -> tuple[bytes, str]:
    img = _open(data)
    if img is None:
        return data, mime
    img = img.convert("RGB")
    img.thumbnail((settings.vision_max_side, settings.vision_max_side))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=82, optimize=True)
    return out.getvalue(), "image/jpeg"
