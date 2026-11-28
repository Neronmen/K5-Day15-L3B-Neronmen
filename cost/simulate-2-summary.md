# Tóm tắt mô phỏng simulate-2@20261128-111131

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| dung_it | 16 | 1 | 2670 | 260 | 0.9 | 8.5 |
| dung_vua | 2 | 1 | 2718 | 223 | 1.0 | 9.0 |
| dung_nhieu | 32 | 1 | 2416 | 227 | 0.9 | 7.9 |

Tỉ lệ đạt dùng để tính: 29/30 (97%) — lượt run-2@20261128-110738

- Tự chọn: lượt run-N mới nhất đã chấm xong, chạy bằng đúng model đang đo (run-2.csv). Muốn dùng lượt khác (vd lượt 2): thêm `--rate-from eval/run-2.csv`.

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (300 người) | Chi phí / tháng — cơ sở (1.000 người) | Chi phí / tháng — cao (3.000 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-6-luna (vào 0.1 · ra 0.5 $/1M) | $0.00037 | $0.00038 | $0.00038 | $3.40 | $11.32 | $33.95 | $0.0113 |
| deepseek-flash (vào 0.3 · ra 1.2 $/1M) | $0.0010 | $0.0011 | $0.0011 | $9.54 | $31.79 | $95.37 | $0.0318 |
| gemini-2.5-flash-lite (vào 0.1 · ra 0.4 $/1M) | $0.00035 | $0.00036 | $0.00036 | $3.18 | $10.60 | $31.79 | $0.0106 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (1.0) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: deepseek-chat. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/50.
