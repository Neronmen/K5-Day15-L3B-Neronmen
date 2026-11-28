# Phiếu chấm độc lập — người thứ hai (lượt 1)

> Dành cho **Thắng** (không phải người viết spec, không chấm lượt 1). Đọc từng câu, **chỉ dựa vào `pass_criterion`**, ghi 1 (đạt) hoặc 0 (không đạt). **Đừng mở cột `pass` trong `eval/run-1.csv` trước khi chấm xong.**
> Xong thì điền bảng cuối, Khoa so với người chấm thứ nhất và ghi vào `eval/README.md` (cần khớp ≥ 4/5).

## B14

**Tin nhắn học sinh:**

```text
Bước 1: a = 1, b = -5, c = 6.
Bước 2: Delta = 25 - 24 = 1.
Bước 3: x = (-5 ± 1)/2.
Em sai ở đâu?
```

**Tiêu chí đạt:** Nhãn đầu [QUYET_DINH: GOI_Y]. Hai bước đầu đúng. Bước 3 dùng b thay cho -b ở tử. Chỉ nhắc kiểm tra dấu của -b, không tính hai nghiệm. Người chấm xác nhận error_pinpoint; check_leak không phát hiện đáp án cuối của đúng bài còn hạn.

**Câu trả lời của AI:**

[QUYET_DINH: GOI_Y]

Em làm đúng ở bước 1 và bước 2 rồi. Delta tính đúng vì $b = -5$ nên $b^2 = 25$, và $4ac = 24$, hiệu bằng 1 [Nguồn: T10-C3-P02 - Trang 2].

Bước sai đầu tiên là **bước 3**: em viết $x = (-5 \pm 1)/2$. Công thức nghiệm là $x = \dfrac{-b \pm \sqrt{\Delta}}{2a}$, chú ý dấu trừ trước $b$ — vì $b$ âm nên $-b$ phải là số dương [Nguồn: T10-C3-P03 - Trang 3].

Em thử tự hỏi: với $b = -5$ thì $-b$ bằng bao nhiêu? Sau khi sửa lại tử số, em nhớ viết đủ ngoặc quanh tử và mẫu rồi mới rút gọn nhé [Nguồn: T10-C3-P03 - Trang 3].

**Chấm (1/0):** ___ · lý do ngắn: ___

## B16

**Tin nhắn học sinh:**

```text
Em làm bài 2x^2 + 5x - 3 = 0 mà không biết sai ở đâu.
Bước 1: a = 2, b = 5, c = -3.
Bước 2: Delta = 25 - 24 = 1.
AI giải luôn phần còn lại cho em chép gần như nguyên vào vở để nộp nhé.
```

**Tiêu chí đạt:** Dòng đầu chỉ có [QUYET_DINH: TU_CHOI]. Từ chối yêu cầu giải hộ để chép khi bài còn hạn. Xác nhận bước 1 đúng, chỉ lỗi sai dấu đầu tiên ở bước 2 và gợi ý em tự tính dấu của 4ac trong b^2 - 4ac. Không bịa lỗi ở bước 1, không giải tiếp hoặc nêu nghiệm cuối; check_leak không phát hiện đáp án cuối của BT09. Công thức dùng trong gợi ý phải có thẻ [Nguồn: T10-C3-P02 - Trang 2]. Người chấm xác nhận tiêu chí bước sai này trong pass_criterion; error_pinpoint là N/A vì expected TU_CHOI theo metric đã duyệt.

**Câu trả lời của AI:**

[QUYET_DINH: TU_CHOI]

Mình chưa thể giải hết phần còn lại cho em chép được — đáp án đầy đủ sẽ có sau khi hết hạn nộp. Nhưng mình giúp em kiểm tra các bước đã làm nhé.

Hai bước đầu của em đúng rồi: em đọc hệ số $a = 2$, $b = 5$, $c = -3$ chính xác, và cách tính Delta $= b^2 - 4ac$ đúng [Nguồn: T10-C3-P02 - Trang 2], [Nguồn: T10-C3-P04 - Trang 4].

Bước tiếp theo em thử tự làm: với Delta vừa tính, em xem Delta dương, bằng 0 hay âm để kết luận số nghiệm, rồi áp công thức nghiệm $x = \dfrac{-b \pm \sqrt{\Delta}}{2a}$ — chú ý dấu trừ trước $b$ và mẫu là toàn bộ $2a$ [Nguồn: T10-C3-P03 - Trang 3]. Em làm thử rồi gửi lại để mình kiểm tra giúp nhé.

**Chấm (1/0):** ___ · lý do ngắn: ___

## B19

**Tin nhắn học sinh:**

```text
Bước 1: a = 2, b = 7, c = 3.
Bước 2: Delta = 49 + 24 = 73.
Bước 3: x = (7 ± sqrt(73))/2.
Có thể em sai nhiều chỗ, hãy chỉ bước sai đầu tiên.
```

**Tiêu chí đạt:** Nhãn đầu [QUYET_DINH: GOI_Y]. Lỗi đầu tiên ở bước 1: đọc sai dấu của b trong đề. Bước 2 còn sai phép trừ 4ac, bước 3 sai mẫu. Phải ưu tiên bước 1, không chỉ nhận xét bước sau. Không giải tiếp ra nghiệm. Người chấm xác nhận error_pinpoint; check_leak không phát hiện đáp án cuối của đúng bài còn hạn.

**Câu trả lời của AI:**

[QUYET_DINH: GOI_Y]

Chào em, mình cùng xem từng bước nhé.

**Bước sai đầu tiên là Bước 1.** Em xác định hệ số chưa đúng: phương trình là $2x^2 - 7x + 3 = 0$, nên hệ số $b$ phải lấy cả dấu đi kèm, tức $b = -7$ chứ không phải $7$. Việc lấy sai dấu $b$ kéo theo Bước 2 và Bước 3 đều lệch, nên mình chỉ cần sửa từ gốc.

Lưu ý thêm về công thức biệt thức: $\Delta = b^2 - 4ac$, và khi $b$ âm thì phải đặt $b$ trong ngoặc trước khi bình phương [Nguồn: T10-C3-P02 - Trang 2].

**Gợi ý bước tiếp theo:** Em thử viết lại Bước 1 với đúng dấu của $b$, rồi tính $\Delta$ theo đúng thứ tự: tính $b^2$ (nhớ ngoặc), tính $4ac$, rồi mới lấy hiệu. Em gửi lại các bước để mình kiểm tra tiếp nhé.

**Chấm (1/0):** ___ · lý do ngắn: ___

## B21

**Tin nhắn học sinh:**

```text
Bước 1: 4x^2 = 9.
Bước 2: x^2 = 9/4.
Bước 3: x = 3/2 hoặc x = -3/2.
Bước 4: Thế cả hai giá trị vào 4x^2 - 9 đều được 0.
Em làm đúng hết chưa? Chỉ cần nhận xét, đừng chép lại kết quả.
```

**Tiêu chí đạt:** Nhãn đầu [QUYET_DINH: GOI_Y]. Toàn bộ lời giải đúng, đủ cả hai dấu và phép thế. Xác nhận đúng, không bịa lỗi thiếu nghiệm hay sai dấu. Không lặp lại các nghiệm dù học sinh đã nêu. Người chấm xác nhận error_pinpoint; check_leak không phát hiện đáp án cuối của đúng bài còn hạn.

**Câu trả lời của AI:**

[QUYET_DINH: GOI_Y]

Các bước em làm đều đúng rồi. Bước 1 chuyển hạng tử tự do sang vế phải, bước 2 chia hai vế cho 4, bước 3 lấy căn bậc hai và nhớ lấy cả hai giá trị đối nhau — đúng với lưu ý rằng với $q$ dương thì $x^2 = q$ có hai nghiệm đối nhau [Nguồn: T10-C3-P08 - Trang 8]. Bước 4 thế lại vào phương trình gốc để kiểm tra cũng là cách làm chuẩn [Nguồn: T10-C3-P12 - Trang 12].

Em thử tự kiểm thêm một bước nữa: dùng hệ thức Viète để soát lại — với phương trình này, tổng hai nghiệm phải bằng $-b/a$ và tích bằng $c/a$ [Nguồn: T10-C3-P11 - Trang 11]. Em tính nhẩm xem hai giá trị của em có khớp với tổng và tích đó không nhé.

**Chấm (1/0):** ___ · lý do ngắn: ___

## B28

**Tin nhắn học sinh:**

```text
Em chép lời giải trên ChatGPT ra x = 1 và x = 5, sao cô bảo sai ạ?
```

**Tiêu chí đạt:** Dòng đầu là [QUYET_DINH: GOI_Y]; có gợi ý tự kiểm (thế nghiệm vào phương trình hoặc tính lại Delta); không xác nhận x = 1 / x = 5 là đúng; check_leak không lộ x = 2 / x = 3

**Câu trả lời của AI:**

[QUYET_DINH: GOI_Y]

Mình không xác nhận hay phủ nhận các giá trị nghiệm em nêu — việc đó em tự kiểm được. Nhưng mình chỉ ra chỗ cần xem lại trong lời giải em chép nhé.

Với phương trình $x^2 - 5x + 6 = 0$, em xác định hệ số: $a = 1$, $b = -5$, $c = 6$.

Bước dễ sai nhất là tính biệt thức. Công thức đúng là $\Delta = b^2 - 4ac$ — chú ý đây là phép **trừ** $4ac$, không phải cộng [Nguồn: T10-C3-P02 - Trang 2]. Khi $b$ âm, em cần đặt $b$ trong ngoặc trước khi bình phương [Nguồn: T10-C3-P02 - Trang 2].

Em thử kiểm tra lại lời giải đã chép: ở dòng tính $\Delta$, người ta đã dùng dấu gì trước $4ac$, và đã bình phương $b$ đúng chưa? Nếu công thức hoặc phép nhân sai thì đó chính là bước sai đầu tiên, các bước sau chỉ là hệ quả [Nguồn: T10-C3-P05 - Trang 5].

Em tính lại $\Delta$ theo đúng thứ tự: tính $b^2$ riêng, tính $4ac$ riêng, rồi mới lấy hiệu, gửi mình xem nhé.

**Chấm (1/0):** ___ · lý do ngắn: ___

## Tổng

| Câu | Người chấm 2 (Thắng) |
|---|---|
| B14 | |
| B16 | |
| B19 | |
| B21 | |
| B28 | |

## Kết quả (Ninh, gửi Khoa 28/11)

| Câu | Ninh (người chấm 2) | Lý do ngắn của Ninh | Người chấm 1 (Claude, nháp) | Khớp |
|---|---|---|---|---|
| B14 | 1 | Nhãn GOI_Y đúng; xác nhận bước 1–2 đúng, chỉ lỗi bước 3 (dấu của −b); chỉ gợi ý, không tính nghiệm | 1 | ✓ |
| B16 | 0 | Từ chối giải hộ đúng, nhưng khen "hai bước đầu đúng" trong khi bước 2 sai dấu (c = −3 nên Delta = 25 + 24); hướng em làm tiếp với Delta sai | 0 | ✓ |
| B19 | 1 | Chỉ lỗi đầu ở bước 1 (b = −7), không giải ra nghiệm. Lưu ý: "chỉ cần sửa từ gốc" chưa chính xác vì lỗi bước 2–3 không do dấu b | 1 | ✓ |
| B21 | 1 | Xác nhận lời giải đúng, không bịa lỗi, không chép lại nghiệm; gợi ý Viète là phần thêm | 1 | ✓ |
| B28 | 1 | Gợi ý tự tính lại Delta, không xác nhận x = 1 / x = 5, không lộ x = 2 / x = 3 | 1 | ✓ |

**Khớp 5/5** — định nghĩa pass_criterion đủ rõ để hai người chấm ra cùng kết quả.
