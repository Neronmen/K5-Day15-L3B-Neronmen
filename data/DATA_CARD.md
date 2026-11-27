# Data card: chương phương trình bậc hai

## Nguồn và cách biên soạn

Toàn bộ dữ liệu là `synthetic`, do Codex hỗ trợ tự biên soạn bằng tiếng Việt ngày 27/11/2026 theo ticket T-01. Không trích hoặc chép sách giáo khoa, tài liệu BTC hay bài làm học sinh. Kiến thức giới hạn ở phương trình bậc hai trong tập số thực. Nội dung được soạn trực tiếp, không dùng bộ sinh ngẫu nhiên nên không có seed ngẫu nhiên.

Nguyễn Hồng Thắng phụ trách kiểm tra và giải thích phần dữ liệu. Kiểm tra tự động dùng phân số chính xác, biệt thức, hệ thức Viète và phép thế vào phương trình gốc. Việc người phụ trách đọc lại toàn bộ nội dung vẫn chờ xác nhận; không coi kiểm tra bằng code là kiểm tay.

## Bài học và hợp đồng truy xuất

`lesson.json` có 16 bản ghi. Chương của lớp giả `10A1` gồm 15 trang, mã `T10-C3-P01` đến `T10-C3-P15`. Một trang riêng `T10B-C3-P01` thuộc lớp giả `10B1` để kiểm tra cách ly lớp. Giữ nguyên schema `code, class_id, page, title, text` và ba mã trang ban đầu. Trang 2 `T10-C3-P02` vẫn là nguồn chính cho câu hỏi "Delta là gì", phù hợp hợp đồng N-02.

Mỗi bản ghi là một trang nội dung logic, không khẳng định tương đương 15 trang A4. Các trang hướng dẫn phương pháp, không chứa lời giải của các bài tập được giao. `search_lesson` chỉ đọc `lesson.json`, lọc theo `class_id`.

## Bài tập và mốc thời gian

`assignments.json` có 13 bản ghi, giữ schema `id, class_id, title, question, due_at, answer_key, final_answers, lesson_codes`. Giữ nguyên ID, đề và hạn của `BT01`, `BT02`. `BT02` yêu cầu tính biệt thức, không yêu cầu tìm nghiệm.

Tại `asked_at = 2026-11-28T21:00:00+07:00`, cũng là mặc định trong `agent.py`:

| Phạm vi | Số bài | ID | Hạn nộp |
|---|---:|---|---|
| Còn hạn, lớp 10A1 | 10 | BT01, BT03 đến BT11 | 05/12/2026 23:59 UTC+7 |
| Đã hết hạn, lớp 10A1 | 2 | BT02, BT12 | 20/11/2026 23:59 UTC+7 |
| Lớp khác 10B1, còn hạn | 1 | BT13 | 05/12/2026 23:59 UTC+7 |

Hạn nộp có múi giờ rõ ràng. Trước hạn là chế độ gợi ý; đúng thời điểm hạn trở đi là hết hạn. `final_answers` gồm số nguyên, số âm Unicode, số thập phân dấu chấm hoặc dấu phẩy, phân số và LaTeX khi thích hợp. Bài vô nghiệm có các cách viết tương ứng.

`answer_key` và `final_answers` là dữ liệu nội bộ. `get_assignment` hiện chỉ trả đề và metadata trước hạn; `final_answers_of` chỉ phục vụ chốt chặn trong code. Không đưa toàn bộ bản ghi bài tập hoặc file JSON vào prompt hay tài liệu tìm kiếm của học sinh còn hạn. Test chặn việc hai trường đáp án lọt vào kết quả `get_assignment` trước hạn.

## Kiểm tra lại

```bash
python -m unittest discover -s tests -p test_data.py -v
python run.py
```

`tests/test_data.py` kiểm schema, ID trùng, liên kết trang theo lớp, thời gian, cách ly dữ liệu, truy vấn Delta và toàn bộ nghiệm bằng tính toán độc lập. Bộ dữ liệu không phải bằng chứng pain, không đại diện chương trình đầy đủ, chưa có nghiệm vô tỉ hoặc số phức. Lọc lớp của retrieval không thay thế kiểm tra quyền truy cập bài tập trong luồng của Khoa.
