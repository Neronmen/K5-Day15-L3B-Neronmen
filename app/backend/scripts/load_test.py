"""Test chịu tải: giả lập N học sinh nộp bài (ảnh hoặc text) trong cùng một lúc.

Chạy (backend đang chạy):
    python scripts/load_test.py --api http://localhost:8000 --students 40
    python scripts/load_test.py --students 40 --image    # nộp ảnh (đi qua kiểm tra độ nét + VLM nếu có)
    python scripts/load_test.py --students 40 --wait-grading   # chờ AI chấm xong, đo thời gian hàng đợi

Lưu ý: nếu backend bật AUTO_GRADE, mỗi bài nộp sẽ gọi model chấm (tốn token).
"""
import argparse
import asyncio
import io
import statistics
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx


def sample_png() -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("L", (900, 600), 235)
    d = ImageDraw.Draw(img)
    for i, line in enumerate(["Cau 1: y' = 5(2x^2 - 3x + 1)^4 (4x - 3)", "Cau 2: y' = 6x cos(3x^2 + 1)",
                              "Cau 3: f'(x) = x / sqrt(x^2 + 4); f'(0) = 0; f'(2) = sqrt(2)/2"]):
        d.text((40, 60 + i * 60), line, fill=10)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def main(a):
    tag = uuid.uuid4().hex[:6]
    async with httpx.AsyncClient(base_url=a.api, timeout=120) as c:
        r = await c.post("/auth/register", json={"email": f"load-gv-{tag}@test.vn", "password": "matkhau123",
                                                  "name": "GV tải", "role": "teacher"})
        r.raise_for_status()
        th = {"Authorization": f"Bearer {r.json()['access_token']}"}
        cls = (await c.post("/teacher/classes", json={"name": f"Lớp tải {tag}", "subject": "Toán"}, headers=th)).json()
        due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        asg = (await c.post(f"/teacher/classes/{cls['id']}/assignments", headers=th, json={
            "title": "Bài kiểm tra tải", "prompt": "Câu 1: Tính đạo hàm y = (2x² − 3x + 1)⁵", "due_at": due,
            "rubric": "Câu 1: 10 điểm"})).json()

        print(f"Tạo {a.students} học sinh…")
        tokens = []
        for i in range(a.students):
            r = await c.post("/auth/register", json={"email": f"load-hs{i}-{tag}@test.vn", "password": "matkhau123",
                                                      "name": f"Học sinh {i + 1}", "role": "student"})
            tokens.append(r.json()["access_token"])
            await c.post("/student/join", json={"class_code": cls["class_code"]}, headers={"Authorization": f"Bearer {tokens[-1]}"})

        img = sample_png() if a.image else None
        lat, errors = [], {}

        async def submit(tok: str):
            t0 = time.perf_counter()
            h = {"Authorization": f"Bearer {tok}"}
            try:
                if img:
                    r = await c.post(f"/student/assignments/{asg['id']}/submit", headers=h,
                                     files={"image": ("vo.png", img, "image/png")})
                else:
                    r = await c.post(f"/student/assignments/{asg['id']}/submit", headers=h,
                                     data={"content": "Câu 1: y' = 5(2x² − 3x + 1)⁴·(4x − 3)"})
                key = str(r.status_code)
            except httpx.HTTPError as e:
                key = type(e).__name__
            lat.append(time.perf_counter() - t0)
            errors[key] = errors.get(key, 0) + 1

        print(f"Nộp {a.students} bài cùng lúc…")
        t0 = time.perf_counter()
        await asyncio.gather(*(submit(t) for t in tokens))
        wall = time.perf_counter() - t0
        lat.sort()
        p95 = lat[int(len(lat) * 0.95) - 1] if lat else 0
        print(f"Xong trong {wall:.2f}s · trung vị {statistics.median(lat):.2f}s · p95 {p95:.2f}s · tối đa {lat[-1]:.2f}s")
        print("Mã phản hồi:", errors, "(201 = nộp thành công)")

        if a.wait_grading:
            print("Chờ AI chấm…")
            t1 = time.perf_counter()
            while time.perf_counter() - t1 < a.timeout:
                rows = (await c.get(f"/teacher/assignments/{asg['id']}/submissions", headers=th)).json()
                st = {}
                for row in rows:
                    st[row["ai_status"]] = st.get(row["ai_status"], 0) + 1
                print("  ", st)
                if not st.get("queued") and not st.get("running"):
                    break
                await asyncio.sleep(5)
            print(f"Hàng đợi chấm xong sau {time.perf_counter() - t1:.0f}s")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--api", default="http://localhost:8000")
    p.add_argument("--students", type=int, default=40)
    p.add_argument("--image", action="store_true")
    p.add_argument("--wait-grading", action="store_true")
    p.add_argument("--timeout", type=int, default=900)
    asyncio.run(main(p.parse_args()))
