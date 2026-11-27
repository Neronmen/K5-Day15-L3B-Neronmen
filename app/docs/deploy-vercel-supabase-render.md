# Deploy nhanh: Vercel (web) + Render (API) + Supabase (DB + file)

```
Trình duyệt ──► Vercel: Next.js (app/frontend)
           └──► Render: FastAPI (app/backend, Docker) ──► Supabase Postgres (+pgvector)
                                                     └──► Supabase Storage (API S3)
```

Không đặt backend trên Vercel: backend có chat stream (SSE), tác vụ chạy nền và thư viện AI nặng, vượt giới hạn serverless.

> **Không dán khoá / mật khẩu vào repo.** Mọi giá trị bí mật chỉ dán trong dashboard của Supabase / Render / Vercel.

## 1. Supabase (khoảng 10 phút)
1. Tạo project mới, chọn vùng **Southeast Asia (Singapore)**. Đặt mật khẩu database và lưu lại.
2. **Database:** nút **Connect** → tab **Session pooler** (cổng **5432**, chạy được với IPv4 của Render) → chép chuỗi kết nối.
   Đổi đầu chuỗi `postgresql://` thành `postgresql+psycopg://` và thay `[YOUR-PASSWORD]`. Đây là `DATABASE_URL`.
   Extension `vector` được Alembic tự bật khi backend khởi động lần đầu.
3. **Storage:** Storage → **New bucket** tên `minutesstudy`, để **Private**.
4. **Khoá S3:** Project Settings → Storage → **S3 Connection** → bật, chép `Endpoint` (`S3_ENDPOINT`), `Region` (`S3_REGION`) → **New access key** → chép `Access key ID` (`S3_ACCESS_KEY`) và `Secret` (`S3_SECRET_KEY`).

## 2. Render (khoảng 10 phút, build lần đầu ~5–8 phút)
1. Render → **New → Blueprint** → kết nối GitHub, chọn repo `K5-Day15-L3B-Neronmen`, nhánh `main`. Render đọc `render.yaml` ở thư mục gốc.
2. Điền các biến Render hỏi: `DATABASE_URL`, `S3_ENDPOINT`, `S3_REGION`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `DEEPSEEK_API_KEY`, và tạm để `CORS_ORIGINS=*` (sửa ở bước 4).
3. **Apply** → chờ build. Xong mở `https://<tên-service>.onrender.com/docs` thấy trang API là chạy.
   Gói free tự ngủ sau 15 phút không dùng; lần gọi đầu mất ~30–50 giây để thức dậy. Mở trang trước khi demo.

## 3. Vercel (khoảng 5 phút)
1. Vercel → **Add New → Project** → chọn repo → **Root Directory** = `app/frontend` (Framework: Next.js tự nhận).
2. Environment Variables: `NEXT_PUBLIC_API_URL` = URL Render ở bước 2 (không có `/` ở cuối).
3. **Deploy** → được URL dạng `https://<tên>.vercel.app`.

## 4. Nối hai đầu
1. Render → service → **Environment** → sửa `CORS_ORIGINS` = URL Vercel (vd `https://minutesstudy.vercel.app`) → **Save** (Render tự deploy lại).
2. Mở URL Vercel → **Đăng ký** tài khoản giáo viên → thấy **Lớp học mẫu - Toán 11** là thông.

## Kiểm nhanh khi lỗi
| Triệu chứng | Xem ở đâu / sửa gì |
|---|---|
| Render build lỗi | Render → Logs. Thường do thiếu biến môi trường |
| API lỗi kết nối DB | `DATABASE_URL` phải là **Session pooler** cổng 5432, đầu `postgresql+psycopg://` |
| Đăng ký giáo viên lỗi 500 | Lưu file lớp mẫu lên Storage: kiểm `S3_ENDPOINT`, `S3_REGION`, khoá, bucket `minutesstudy` đã tạo |
| Web báo lỗi mạng / CORS | `CORS_ORIGINS` trên Render phải đúng URL Vercel; `NEXT_PUBLIC_API_URL` trên Vercel phải đúng URL Render (đổi biến xong phải **Redeploy** Vercel) |
| AI không trả lời | Thiếu / sai `DEEPSEEK_API_KEY` |
