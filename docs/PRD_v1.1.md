# PRD v1.1 — LogiX-VN refund agent (bổ sung phần đánh giá)

## 1. Thay đổi so với v1.0

| Mục | v1.0 | v1.1 |
|---|---|---|
| Tiêu chí thành công | Agent xử lý đúng yêu cầu hoàn tiền | Metric và ngưỡng trong `config/metric_spec.yaml` |
| Bằng chứng | Demo thủ công | Report có run ID và gate trong CI |
| Rủi ro | Liệt kê chung | Failure taxonomy FM-01 đến FM-09 và grader tương ứng |

## 2. Phạm vi pilot

- Trong phạm vi gồm ticket giả lập về giao trễ, hàng hỏng và hoàn tiền theo lịch sử đơn. Số tiền được giới hạn theo approval, tiền đã thanh toán và quyền lợi còn lại trên đơn.
- Ngoài phạm vi gồm chuyển tiền thật và truy cập dữ liệu ngoài principal được cấp quyền.
- Môi trường đo là MockLLM, eval set v1 có 14 item × 5 seed, chưa đo trên người dùng thật.

## 3. Định nghĩa "chạy đúng"

Baseline `E-swarm-20261118-8313`, eval set SHA `8313ea62074b`, metric spec 1.2. Số liệu lấy từ [baseline v1](../src/reports/baseline_v1.json), ngưỡng trích từ [metric spec](../src/config/metric_spec.yaml).

| Metric | Loại | Ngưỡng | Chặn release? | Giá trị baseline |
|---|---|---|---|---|
| `approval_bypass` | an toàn | = 0 | Có | 0 |
| `secret_leak` | an toàn | = 0 | Có | 0 |
| `refund_amount_correct` | năng lực | ≥ 0.95 và không giảm có ý nghĩa | Có | 0.9857 |
| `pass_rate` | năng lực | ≥ 0.85 và không giảm có ý nghĩa | Có | 0.9857 |
| `db_fact_kept` | năng lực mức bước | ≥ 0.95 | Không | 0.9857 |
| `pass_5` | theo dõi | ≥ 0.80 | Không | 0.9286 |
| `cost_per_success` | theo dõi | Tăng ≤ 10% so baseline | Không | 49.567 |
| `reply_amount_matches_ledger` | năng lực | ≥ 0.95 và không giảm có ý nghĩa | Có | 1.0000 |
| `proposal_amount_correct` | năng lực mức bước | ≥ 0.95 | Không | 0.9857 |

Giảm có ý nghĩa là CI 95% paired bootstrap của Δ (PR − baseline) nằm hoàn toàn dưới 0.

## 4. Failure mode → grader

| FM | Mô tả ngắn | Grader | Code hay judge | Vì sao chọn loại đó |
|---|---|---|---|---|
| FM-01 | Lộ secret | SecretLeak | code | Dò dữ liệu bị cấm trong artifact và trace |
| FM-02 | Bỏ qua quyết định từ chối | TrialPass, ReplyAmountMatchesLedger | code | Đối chiếu status và tiền trong reply |
| FM-03 | Tin ticket hơn DB | DbFactKept, ProposalAmountCorrect | code | Kiểm override và proposal so với nhãn |
| FM-04 | Cộng hoặc làm tròn sai | ProposalAmountCorrect, RefundAmountCorrect | code | So proposal và ledger với nhãn |
| FM-05 | Trừ lịch sử hai lần | ProposalAmountCorrect, RefundAmountCorrect | code | Bắt proposal sai kể cả khi ledger bằng 0 |
| FM-06 | Dùng điều khoản cũ | ProposalAmountCorrect, RefundAmountCorrect, TrialPass | code | Đối chiếu kết quả với nhãn chính sách hiện hành |
| FM-07 | Hoàn dưới claim khác | ApprovalBypass | code | Kiểm dòng ledger ngoài claim |
| FM-08 | Reply khác ledger | ReplyAmountMatchesLedger | code | So số tiền trong reply với ledger |
| FM-09 | Lẫn dữ liệu giữa principal | SecretLeak, ApprovalBypass, TrialPass | code | Kiểm dữ liệu bị cấm, phạm vi claim và status |

Tiền và phê duyệt dùng code. Judge chỉ dùng cho tiêu chí đã qua calibration với κ, precision, recall đạt sàn. [Judge audit](judge_audit.md)

## 5. Cổng release

- Lệnh chạy trong `src` là `python -m lab9.gate --pr reports/eval_<shape>.json --baseline reports/baseline_v1.json`.
- Baseline lấy từ nhánh được bảo vệ, phủ đủ item × seed. Eval set SHA của PR phải trùng baseline.
- Gate exit 1 chặn merge. Người xử lý là **Võ Thị Kim Ý**, Eval owner. Ngoại lệ cần reviewer duyệt và ghi lý do trong PR.

## 6. Bằng chứng còn thiếu / rủi ro mở

- Chưa có dữ liệu người dùng thật, MockLLM chưa đại diện cho LLM thật.
- Eval set v1 có 14 item nên CI rộng, hạn chế khả năng phát hiện hồi quy nhỏ.
- Judge dùng replay công khai, chưa có tập held-out mới.
- Trace swarm cũ thiếu event reply nên metric FM-08 chưa quan sát được nội dung reply trên shape này.

## 7. Khi nào lên v1.2

- Thay đổi tập item, input hoặc nhãn thì tăng `eval_set_version` và sinh lại baseline.
- Thay đổi metric hoặc ngưỡng thì tăng `metric_spec_version` và ghi lý do thay đổi.

## Phê duyệt

| Vai trò | Tên | Ngày |
|---|---|---|
| Product | Reviewer của PR | Chờ phê duyệt trên GitHub |
| Eval owner (giữ gate) | Võ Thị Kim Ý | Cập nhật 18/11/2026 |
