"""Dựng video demo: ảnh chụp web thật + zoom mượt + phụ đề + giọng đọc tiếng Việt (edge-tts) → demo.mp4 (1920x1080, 30fps)."""
import asyncio
import math
import re
import subprocess
import sys
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
SHOTS, TMP = ROOT / "shots", ROOT / "build"
TMP.mkdir(exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1920, 1080, 30
VOICE, RATE = "vi-VN-HoaiMyNeural", "+12%"
FADE = 0.4
F = "C:/Windows/Fonts/"
BG, ACCENT, INK, MUTED = (17, 19, 18), (245, 190, 70), (240, 238, 232), (160, 160, 150)

# (ảnh hoặc "TITLE"/"END", lời đọc, phụ đề, (zoom đầu, zoom cuối), tâm zoom)
SCENES = [
    ("TITLE", "Mười bốn trên hai mươi sáu học sinh được khảo sát chép gần như nguyên lời giải. "
              "MinutesStudy Tutor là gia sư không làm hộ.", None, (1, 1), (960, 540)),
    ("03_typed", "Minh gửi bài làm có bước sai.", "Học sinh gửi bài làm — bài còn hạn nộp", (1.0, 1.22), (1460, 560)),
    ("04_pinpoint", "Gia sư chỉ đúng bước sai đầu tiên, và không đưa đáp án.",
     "Chỉ đúng bước sai đầu tiên · không đưa đáp án", (1.22, 1.42), (1450, 590)),
    ("05_pdf", "Mỗi ý đều trích đúng trang bài giảng của cô.",
     "Trích đúng trang tài liệu giáo viên · bấm là mở", (1.0, 1.28), (800, 400)),
    ("06_attack", "Giả làm giáo viên để xin đáp án? Vẫn bị từ chối, vì hạn nộp do máy chủ quyết định.",
     "Giả làm giáo viên, chèn lệnh giả → không đổi chế độ", (1.2, 1.42), (1450, 690)),
    ("07_solve", "Hết hạn nộp, gia sư mới giải chi tiết.",
     "Bài đã hết hạn → mới giải chi tiết", (1.12, 1.32), (1450, 580)),
    ("08_cross", "Dán đề bài khác còn hạn vào? Code chặn ngay.",
     "Dán đề bài khác còn hạn → code soi câu trả lời và chặn", (1.18, 1.4), (1450, 430)),
    ("09_teacher", "Cô giáo thấy ngay em nào đang tìm đáp án.",
     "Giáo viên thấy ngay tin nhắn bị gắn cờ", (1.1, 1.38), (1100, 450)),
    ("END", "Ba mươi câu thử, A I thật: hai mươi tám câu đạt, không câu nào lộ đáp án.", None, (1, 1), (960, 540)),
]


def font(name, size):
    return ImageFont.truetype(F + name, size)


def card(kind):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # nền: lưới mờ kiểu "bảng & phấn" + quầng sáng vàng
    for x in range(0, W, 64):
        d.line([(x, 0), (x, H)], fill=(24, 27, 25))
    for y in range(0, H, 64):
        d.line([(0, y), (W, y)], fill=(24, 27, 25))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W // 2 - 520, H // 2 - 360, W // 2 + 520, H // 2 + 360], fill=(70, 52, 14))
    im = Image.blend(im, Image.composite(glow, im, glow.convert("L").point(lambda v: 255 if v else 0)).filter(
        ImageFilter.GaussianBlur(160)), 0.55)
    d = ImageDraw.Draw(im)

    def center(text, y, f, fill):
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=fill)

    if kind == "TITLE":
        center("TRACK F · NHÓM NERONMEN · AI20K", 300, font("arialbd.ttf", 30), ACCENT)
        center("MinutesStudy Tutor", 360, font("arialbd.ttf", 104), INK)
        center("Gia sư AI chỉ ra bước sai — không lộ đáp án khi bài còn hạn", 500, font("arial.ttf", 44), MUTED)
        d.rounded_rectangle([W / 2 - 420, 620, W / 2 + 420, 740], 28, fill=(32, 30, 22), outline=ACCENT, width=3)
        center("14/26 học sinh chép nguyên lời giải", 645, font("arialbd.ttf", 46), ACCENT)
        center("Khảo sát học sinh lớp 10–12, n = 26", 760, font("arial.ttf", 28), MUTED)
    else:
        center("KẾT QUẢ ĐO · LƯỢT 1 · AI THẬT (DEEPSEEK)", 250, font("arialbd.ttf", 30), ACCENT)
        stats = [("28/30", "câu thử đạt"), ("0", "câu lộ đáp án"), ("4/4", "câu cần từ chối đều đạt")]
        for i, (big, small) in enumerate(stats):
            cx = W / 2 + (i - 1) * 470
            d.rounded_rectangle([cx - 200, 330, cx + 200, 590], 30, fill=(28, 30, 27), outline=(60, 60, 50), width=2)
            fb = font("arialbd.ttf", 110)
            d.text((cx - d.textlength(big, font=fb) / 2, 360), big, font=fb, fill=ACCENT if i != 1 else (120, 210, 140))
            fs = font("arial.ttf", 36)
            d.text((cx - d.textlength(small, font=fs) / 2, 505), small, font=fs, fill=INK)
        center("MinutesStudy Tutor", 690, font("arialbd.ttf", 64), INK)
        center("Nhóm Neronmen · github.com/Neronmen/K5-Day15-L3B-Neronmen", 785, font("arial.ttf", 32), MUTED)
    return im


def caption_layer(text):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font("arialbd.ttf", 44)
    tw = d.textlength(text, font=f)
    x0, y0 = (W - tw) / 2 - 48, H - 150
    d.rounded_rectangle([x0, y0, x0 + tw + 96, y0 + 92], 22, fill=(12, 13, 12, 228), outline=(245, 190, 70, 255), width=3)
    d.text((x0 + 48, y0 + 20), text, font=f, fill=INK)
    # nhãn góc: chứng thực là AI thật
    fb = font("arialbd.ttf", 24)
    tag = "● AI THẬT · DEEPSEEK · WEB MINUTESSTUDY"
    d.rounded_rectangle([36, 30, 76 + d.textlength(tag, font=fb), 92], 16, fill=(10, 11, 10, 255), outline=(120, 210, 140, 255), width=2)
    d.text((56, 47), tag, font=fb, fill=(120, 210, 140))
    return layer


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def frame(base, z, c):
    cw, ch = W / z, H / z
    x = min(max(c[0] - cw / 2, 0), W - cw)
    y = min(max(c[1] - ch / 2, 0), H - ch)
    return base.resize((W, H), Image.LANCZOS if z > 1.01 else Image.BILINEAR, box=(x, y, x + cw, y + ch))


async def tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(path))


def duration(path):
    out = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    durs = []
    for i, (_, vo, *_rest) in enumerate(SCENES):
        p = TMP / ("vo%02d.mp3" % i)
        asyncio.run(tts(vo, p))
        durs.append(duration(p))
    lens = [d + 0.4 for d in durs]
    lens[0] += 0.3
    lens[-1] += 1.2
    starts = [sum(lens[:i]) for i in range(len(lens))]
    total = sum(lens)
    print("tổng %.1f giây" % total, [round(x, 1) for x in lens])

    bases, caps = [], []
    for img, _, cap, *_r in SCENES:
        bases.append(card(img) if img in ("TITLE", "END") else Image.open(SHOTS / (img + ".png")).convert("RGB").resize((W, H)))
        caps.append(caption_layer(cap) if cap else None)

    def render(i, t_local):
        img, _, cap, (z0, z1), c = SCENES[i]
        z = z0 + (z1 - z0) * ease(t_local / lens[i])
        im = frame(bases[i], z, c)
        if caps[i] is not None:
            a = min(1.0, t_local / 0.35)
            layer = caps[i] if a >= 1 else Image.fromarray(__import__("numpy").array(caps[i])) if False else caps[i]
            im = im.convert("RGBA")
            if a < 1:
                layer = caps[i].copy()
                layer.putalpha(caps[i].getchannel("A").point(lambda v: int(v * a)))
            im = Image.alpha_composite(im, layer).convert("RGB")
        return im

    video = TMP / "video.mp4"
    proc = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                             "-pix_fmt", "yuv420p", str(video)], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for k in range(n):
        t = k / FPS
        i = max(j for j in range(len(starts)) if starts[j] <= t)
        im = render(i, t - starts[i])
        # chuyển cảnh: hoà dần sang cảnh sau trong FADE giây cuối
        if i + 1 < len(SCENES) and t > starts[i + 1] - FADE:
            a = (t - (starts[i + 1] - FADE)) / FADE
            im = Image.blend(im, render(i + 1, 0), ease(a))
        if k < 12:  # mở đầu từ đen
            im = Image.blend(Image.new("RGB", (W, H)), im, k / 12)
        if k > n - 18:  # kết thúc về đen
            im = Image.blend(im, Image.new("RGB", (W, H)), (k - (n - 18)) / 18)
        proc.stdin.write(im.tobytes())
        if k % 150 == 0:
            print("  khung %d/%d" % (k, n), flush=True)
    proc.stdin.close()
    proc.wait()

    # ghép giọng đọc đúng thời điểm từng cảnh
    args = [FF, "-y", "-loglevel", "error", "-i", str(video)]
    for i in range(len(SCENES)):
        args += ["-i", str(TMP / ("vo%02d.mp3" % i))]
    delays = "".join("[%d:a]adelay=%d|%d[a%d];" % (i + 1, (starts[i] + (0.5 if i == 0 else 0.15)) * 1000,
                                                     (starts[i] + (0.5 if i == 0 else 0.15)) * 1000, i)
                     for i in range(len(SCENES)))
    mix = "".join("[a%d]" % i for i in range(len(SCENES))) + "amix=inputs=%d:normalize=0,volume=1.6,apad[aout]" % len(SCENES)
    out = ROOT / "MinutesStudy_Tutor_demo.mp4"
    args += ["-filter_complex", delays + mix, "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac",
             "-b:a", "192k", "-shortest", str(out)]
    subprocess.run(args, check=True)
    print("XONG:", out, "%.1f giây" % total)


if __name__ == "__main__":
    sys.exit(main())
