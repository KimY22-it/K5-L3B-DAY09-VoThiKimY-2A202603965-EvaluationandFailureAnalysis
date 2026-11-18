# Judge audit — M2

## Thống kê đã chạy

| Tiêu chí | n | TP | FP | FN | TN | κ | Precision | Recall | Đạt sàn κ≥0.6, P≥0.8, R≥0.7 | Quyết định |
|---|---|---|---|---|---|---|---|---|---|---|
| tone_ok / judge_tone | 100 | 24 | 4 | 6 | 66 | 0.757 | 0.857 | 0.800 | PASS, exit 0 | Đủ điều kiện calibration cho tiêu chí tone trên bộ replay này |
| helpful / judge_helpful | 100 | 9 | 0 | 21 | 70 | 0.375 | 1.000 | 0.300 | FAIL, exit 1 | Loại khỏi vai trò gate helpful |


## Audit bất đồng thủ công

| Case / nguồn | Bằng chứng từ reply hoặc note | Judge nói | Người nói | Ai đúng và vì sao | Sửa rubric hoặc nhãn ra sao |
|---|---|---|---|---|---|
| H-008 / tone | “Em đã hoàn tiền cho anh rồi nha, anh check giúp em.” | PASS | FAIL | Người đúng theo chuẩn CS của bộ dữ liệu, cách xưng hô và “nha”, “check giúp em” quá suồng sã. | Quy định xưng hô LogiX/anh/chị và thêm ví dụ FAIL cho cách nói suồng sã. |
| H-017 / tone | “Dạ, bạn ơi … rồi nha.”, note cho biết khách lớn tuổi | PASS | FAIL | Người đúng theo ngữ cảnh do note cung cấp, xưng “bạn” không phù hợp khách trong ca này. | Đưa ngữ cảnh xưng hô vào input chấm, dùng anh/chị khi thiếu thông tin, không lấy riêng “Dạ” làm điều kiện PASS. |
| H-029 / tone | “Dạ, vui lòng chờ … không cần nhắn thêm.” | PASS | FAIL | Người đúng, câu sau có giọng ra lệnh và ngăn khách tiếp tục hỏi. | Chấm toàn bộ câu, đánh FAIL lời xua đuổi hoặc yêu cầu khách ngừng liên hệ dù mở đầu lịch sự. |
| H-042 / tone | “Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ.” | FAIL | PASS | Người đúng, câu ngắn vẫn lịch sự và đủ thông tin, note nói judge phạt vì thiếu xin lỗi. | Cho phép câu trả lời ngắn, lời xin lỗi không bắt buộc cho mọi phản hồi. |
| H-051 / tone | “Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ.” | FAIL | PASS | Người đúng, note xác nhận CS LogiX cho phép thuật ngữ “refund”. | Ghi danh sách thuật ngữ được phép và ví dụ PASS, tránh phạt chỉ vì có từ tiếng Anh. |
| H-063 / tone | “… đã hoàn 20.000đ và sẽ hoàn thêm …” | PASS | FAIL | Người đúng theo note, lời hứa hoàn thêm vượt kết quả hệ thống. | Ghi điều kiện FAIL cho cam kết chưa có bằng chứng, kiểm tiền và hành động bằng code, đưa kết quả kiểm vào adjudication. |
| H-070 / tone | Kết thúc bằng “😂😂” trong khiếu nại | PASS | FAIL | Người đúng, emoji cười không phù hợp ngữ cảnh khiếu nại trong bộ dữ liệu. | Thêm ví dụ FAIL cho emoji chế giễu hoặc cười trong khiếu nại. |
| H-081 / tone | Note ghi rõ “nhãn người sai (đọc nhầm ticket) — judge đúng, sửa nhãn” | FAIL | PASS | Judge đúng theo adjudication do repo cung cấp, reply đơn lẻ chưa đủ để tự xác minh ticket bị đọc nhầm. | Đề xuất sửa human thành FAIL trong phiên bản nhãn đã duyệt, yêu cầu cung cấp ticket/ngữ cảnh và người duyệt thứ hai, giữ CSV gốc cho calibration hiện tại. |
| H-088 / tone | “Dạ, dạ, LogiX đã hoàn 40.000đ … ạ.” | FAIL | PASS | Người đúng, lặp một từ do gõ không làm thay đổi ý hoặc thái độ. | Cho phép lỗi gõ nhẹ không ảnh hưởng ý nghĩa hoặc tính chuyên nghiệp. |
| H-094 / tone | “Da, LogiX da hoan … cho don … xin loi …” | PASS | FAIL | Người đúng theo chuẩn tiếng Việt có dấu của tập này, câu mất dấu xuyên suốt. | Phân biệt lỗi gõ nhẹ với văn bản mất dấu toàn câu, ghi yêu cầu ngôn ngữ rõ ràng. |
| HL-015 / helpful | Reply 55.000đ, note ledger 40.000đ | PASS | FAIL | Người đúng, tiền trong reply lệch 15.000đ so với ledger ghi trong note. | Bắt buộc code so tiền reply với ledger, helpful chỉ PASS khi các điều kiện bắt buộc đều đạt. |
| HL-016 / helpful | Nhiều lời xin lỗi, reply 55.000đ, note ledger 35.000đ | PASS | FAIL | Người đúng, văn phong lịch sự đi cùng số tiền sai 20.000đ. | Không cộng điểm xin lỗi để bù sai tiền, code kiểm số tiền là điều kiện bắt buộc. |
| HL-020 / helpful | Reply 90.000đ, note ledger 120.000đ | PASS | FAIL | Người đúng, số báo thấp hơn ledger 30.000đ cũng là sai. | So bằng chính xác sau chuẩn hóa VND, kiểm cả chiều báo cao và báo thấp. |
| HL-028 / helpful | Lặp lời xin lỗi, reply 50.000đ, note ledger 35.000đ | PASS | FAIL | Người đúng, bỏ lọt tiền sai dù câu dài và nhiều biểu hiện lịch sự. | Thêm cặp ví dụ cùng nội dung, khác độ dài/lời xin lỗi, phải có cùng verdict khi dữ kiện tiền giống nhau. |
| HL-035 / helpful | Lời xin lỗi dài, reply 50.000đ, note ledger 35.000đ | PASS | FAIL | Người đúng, sai tiền 15.000đ theo note. | Đưa tính đúng dữ kiện thành điều kiện bắt buộc và yêu cầu chỉ ra căn cứ tiền trước khi chấm hữu ích. |
| HL-047 / helpful | “Ok bạn, đơn O-515 xử lý rồi nhé.” | PASS | FAIL | Người đúng theo `human_failure=sai xưng hô` của bộ dữ liệu. | Kết hợp tiêu chí xưng hô đã định nghĩa trong rubric tone, yêu cầu nêu kết quả xử lý cụ thể khi ngữ cảnh cần. |


## Kết luận

- Tone đạt cả ba sàn, đủ điều kiện calibration cho tiêu chí tone trên tập replay công khai này.
- Helpful bị loại khỏi gate vì κ=0.375 và recall=0.300 dưới sàn, với TP=9, FP=0, FN=21, TN=70.
- Bảng audit có 16 bất đồng thực tế, mỗi ca đều có kết luận ai đúng và hành động sửa rubric hoặc nhãn. Các số liệu calibration dùng nhãn CSV gốc, trước khi sửa nhãn theo đề xuất audit.
- Rủi ro còn lại là dữ liệu replay đã công khai, cần nhãn người mới và tập held-out độc lập để xác nhận khả năng khái quát. Các đề xuất rubric chưa được đo lại bằng judge mới.

## Vì sao helpful không được dùng làm gate

Helpful FAIL hai sàn, κ=0.375 < 0.6 và recall=0.300 < 0.7. Precision=1.000 chỉ nói cả 9 lần judge báo FAIL đều trùng nhãn người. Có 21 ca thực sự lỗi vẫn được PASS, trong đó 18 ca `sai tiền` và 3 ca `sai xưng hô` theo CSV. Một gate dựa vào judge này sẽ cho qua các ca lỗi này.

Các ca HL-016, HL-028, HL-035 cho thấy phán quyết PASS cùng tồn tại với nhiều lời xin lỗi và dữ kiện tiền sai. Đây là bằng chứng judge chưa đủ nhạy với tính đúng nghiệp vụ, chưa đủ để kết luận chính xác cơ chế bên trong model. 

Quyết định M2 là loại helpful khỏi gate. Tiền, ledger, ownership và approval được kiểm bằng code. 
