# Tóm tắt mô phỏng simulate-1@20261127-211403

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| dung_it | 16 | 1 | 1798 | 236 | 0.9 | 6.6 |
| dung_vua | 2 | 1 | 1832 | 151 | 1.0 | 7.0 |
| dung_nhieu | 32 | 1 | 1631 | 188 | 0.9 | 6.2 |

Tỉ lệ đạt dùng để tính: **chưa có** lượt eval nào chấm xong (`python run.py score eval/run-N.csv`) → chưa tính được chi phí / task thành công

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (300 người) | Chi phí / tháng — cơ sở (1.000 người) | Chi phí / tháng — cao (3.000 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-6-luna (vào 0.1 · ra 0.5 $/1M) | $0.00027 | — | — | $2.46 | $8.19 | $24.56 | $0.0082 |
| deepseek-flash (vào 0.3 · ra 1.2 $/1M) | $0.00075 | — | — | $6.83 | $22.78 | $68.33 | $0.0228 |
| gemini-2.5-flash-lite (vào 0.1 · ra 0.4 $/1M) | $0.00025 | — | — | $2.28 | $7.59 | $22.78 | $0.0076 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (1.0) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: gpt-6-luna. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/50.
