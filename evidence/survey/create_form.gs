/**
 * Tạo Google Form khảo sát từ evidence/survey/questions.md (giữ nguyên văn câu hỏi).
 * Cách chạy: https://script.google.com → Dự án mới → dán toàn bộ file này → chọn hàm createSurvey → Chạy
 * → cấp quyền → xem link ở "Nhật ký thực thi" (Execution log).
 * Form không thu email, không bắt đăng nhập (người trả lời là trẻ vị thành niên, ẩn danh).
 */
function createSurvey() {
  var form = FormApp.create('Lần gần nhất em gặp bài tập khó ở nhà');
  form.setDescription(
    'Chào em! Nhóm anh chị đang tìm hiểu cách các bạn học sinh làm bài tập ở nhà. ' +
    'Form khoảng 2 phút, hoàn toàn ẩn danh, không hỏi tên hay trường. ' +
    'Không có câu trả lời đúng hay sai, em cứ trả lời thật nhé. Cảm ơn em!'
  );
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false); // true sẽ bắt đăng nhập Google → mất ẩn danh
  form.setAllowResponseEdits(false);
  form.setProgressBar(true);
  form.setConfirmationMessage('Cảm ơn em đã trả lời!');

  // Câu 1 — "Khác" → kết thúc form
  var q1 = form.addMultipleChoiceItem().setTitle('Em đang học lớp').setRequired(true);
  var page2 = form.addPageBreakItem().setTitle('Bài tập về nhà');
  q1.setChoices([
    q1.createChoice('10', page2),
    q1.createChoice('11', page2),
    q1.createChoice('12', page2),
    q1.createChoice('Khác', FormApp.PageNavigationType.SUBMIT)
  ]);

  // Câu 2
  form.addMultipleChoiceItem()
    .setTitle('Lần gần nhất em gặp một bài tập về nhà mà không tự làm được là khi nào?')
    .setChoiceValues(['Hôm nay / hôm qua', 'Trong tuần này', 'Tuần trước', 'Lâu hơn', 'Chưa bao giờ'])
    .setRequired(true);

  // Câu 3 — chọn nhiều
  form.addCheckboxItem()
    .setTitle('Lần đó em đã làm gì?')
    .setHelpText('Chọn nhiều')
    .setChoiceValues([
      'Chụp ảnh lên app giải bài', 'Hỏi ChatGPT / chatbot', 'Tìm lời giải trên mạng', 'Hỏi bạn',
      'Hỏi bố mẹ, anh chị', 'Hỏi thầy cô / gia sư', 'Xem lại vở, sách', 'Bỏ qua bài đó'
    ])
    .setRequired(true);

  // Câu 4 — chọn một
  form.addMultipleChoiceItem()
    .setTitle('Nếu đã dùng app / chatbot / mạng: em đã dùng lời giải đó thế nào?')
    .setHelpText('Chọn một')
    .setChoiceValues([
      'Chép gần như nguyên vào bài', 'Đọc hiểu rồi tự viết lại', 'Chỉ xem đáp số để so',
      'Xem gợi ý một bước rồi tự làm', 'Không dùng'
    ])
    .setRequired(true);

  // Câu 5
  form.addMultipleChoiceItem()
    .setTitle('Trong 1 tuần qua, em dùng app giải bài / chatbot cho bài tập về nhà khoảng mấy lần?')
    .setChoiceValues(['0', '1–2', '3–5', '6–10', 'Trên 10'])
    .setRequired(true);

  // Câu 6
  form.addMultipleChoiceItem()
    .setTitle('Lần gần nhất có bài kiểm tra cùng dạng với bài em đã xem lời giải, em làm được không?')
    .setChoiceValues(['Làm được hết', 'Làm được một phần', 'Không làm được', 'Chưa có bài kiểm tra như vậy'])
    .setRequired(true);

  // Câu 7 — chọn nhiều, có "Khác"
  form.addCheckboxItem()
    .setTitle('Vì sao em dùng lời giải có sẵn thay vì tự làm tiếp?')
    .setHelpText('Chọn nhiều')
    .setChoiceValues([
      'Không biết bắt đầu từ đâu', 'Làm sai mà không biết sai ở đâu', 'Quá nhiều bài, không đủ thời gian',
      'Không có ai để hỏi lúc đó', 'Chỉ cần nộp cho đủ'
    ])
    .showOtherOption(true)
    .setRequired(true);

  // Câu 8
  form.addMultipleChoiceItem()
    .setTitle('Nếu có người chỉ cho em bước nào sai và gợi ý bước tiếp (không đưa đáp án), em có muốn tự làm tiếp không?')
    .setChoiceValues(['Có', 'Tuỳ bài', 'Không, em muốn có đáp án luôn'])
    .setRequired(true);

  // Câu 9 — không bắt buộc
  form.addParagraphTextItem()
    .setTitle('Kể ngắn lần gần nhất em bí một bài ở nhà (môn gì, bí ở đâu, em đã làm gì)')
    .setHelpText('Không bắt buộc. Đừng ghi tên người hay trường.')
    .setRequired(false);

  // Bảng tính nhận câu trả lời (để xuất CSV → results.csv)
  var ss = SpreadsheetApp.create('Kết quả — Lần gần nhất em gặp bài tập khó ở nhà');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  Logger.log('Link gửi học sinh: ' + form.getPublishedUrl());
  Logger.log('Link sửa form:     ' + form.getEditUrl());
  Logger.log('Bảng kết quả:      ' + ss.getUrl());
}
