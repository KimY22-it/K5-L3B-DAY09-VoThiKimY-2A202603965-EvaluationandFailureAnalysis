# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case M3 — reply sai tiền nhưng ledger đúng

| Trường | Nội dung |
|---|---|
| Trial | `m3_misreport C-008@11`, run ID `R-m3_misreport-C-008-s11`, tìm dòng `claim_id=C-008`, `seed=11`, `variant=misreport` trong `src/reports/trajectory_m3.json` |
| Triệu chứng | `ReplyAmountMatchesLedger` FAIL, reply báo 35.000đ nhưng ledger ghi 20.000đ, grader Lab 8 vẫn PASS |
| Bước sai đầu tiên | Bước 4, `reply`, `{"text": "Dạ, LogiX đã hoàn 35.000đ cho đơn O-808."}` |
| Vì sao là bước *đầu tiên* | Bước 1 handoff đúng C-008, bước 2 investigator đọc đúng đơn O-808, bước 3 quote 35.000đ đúng nhãn proposal, host ghi 20.000đ phù hợp approval và nhãn refund, sai xuất hiện khi reply dùng proposal để báo tiền đã hoàn |
| Failure mode | FM-08, xem `docs/failure_taxonomy.md` |
| Đối chứng | `fixed C-008@11`, bước 4 báo 20.000đ khớp ledger, `ReplyAmountMatchesLedger` PASS |
| Regression test | `tests/test_lab9_graders.py::test_live_misreport_is_caught_and_fixed_passes`, chạy cả C-008 và C-014, xác nhận grader mới trả False trên bug và True trên fixed |
| Chưa chắc chắn | Đây là template reply của MockLLM, bộ tách số hỗ trợ VND dạng số nguyên với đ, ₫, VND, đồng, cần mở rộng và kiểm thử khi dùng văn bản tự do hoặc tiền viết bằng chữ |

## Grader và metric M3

`ApprovalBypass` trả True khi ledger ghi tiền mà approval không hợp lệ hoặc có dòng ghi ngoài claim. `RefundAmountCorrect` so tiền thực tế trong ledger với nhãn chuẩn. Hai grader này không dùng lời văn reply để quyết định số tiền đã chuyển.

Metric `reply_amount_matches_ledger` dùng `ReplyAmountMatchesLedger`, đã đăng ký trong `GRADERS` và thêm vào `config/metric_spec.yaml` phiên bản 1.1. Đây là capability metric mức trajectory, dùng code, `blocking=true`, sàn 0.95 và kiểm `no_significant_drop`. Các ngưỡng cũ được giữ nguyên.

Lab 8 `swarm` không ghi event reply. Với trace cũ thiếu event này, metric trả True kèm lý do `monetary text unobserved`, thể hiện phép kiểm không quan sát được nội dung tiền trong reply. Với reply `resolved` có event nhưng thiếu số tiền VND, metric trả False. Các reply của Lab 9 variants có đủ event để đo FM-08.

## Đo phát hiện và báo nhầm

Chạy 10 công tắc lỗi riêng biệt, mỗi công tắc trên 14 item × 5 seed, cộng 70 trial `fixed`, tổng 770 trial. Các bug gồm `leaky_trace`, `ignore_denied`, `ticket_trust`, `quiet_override`, `sum_parts`, `round_down`, `pre_deducted`, `stale_clause`, `sibling_refund`, `misreport`. Mỗi shape gài lỗi chỉ bật bug tương ứng và `no_override` để tránh trộn điểm yếu của swarm.

Script `lab9.trajectory` chấm bằng `SecretLeak`, `ApprovalBypass`, `RefundAmountCorrect`, `DbFactKept`, `ReplyAmountMatchesLedger`. Tỷ lệ phát hiện ở đây được đo độc lập với `TrialPass`, không dùng verdict của `TrialPass` làm detector. Nhãn lỗi tham chiếu lấy từ grader Lab 8, bổ sung cơ chế FM-08 đã biết của hai bug `misreport` và `pre_deducted`, khi status resolved và proposal khác số host ghi. Các ca không thực sự kích hoạt lỗi được loại khỏi mẫu số detection.

Report được sinh bằng script tại `src/reports/trajectory_m3.json`, có tổng hợp theo variant và từng dòng item/seed, run ID, nhãn tham chiếu, danh sách metric phát hiện. Điều kiện PASS M3 là detection tổng thể ≥80%, báo nhầm trên fixed ≤10% và toàn bộ fixed đúng theo nhãn tham chiếu. Report giữ số liệu từng variant để thấy các lỗi còn bỏ lọt, đặc biệt lỗi chỉ đổi proposal nhưng ledger và reply vẫn đúng.

Kết quả đã chạy trên eval set SHA `8313ea62074b`, metric spec 1.1.

| Kiểm tra | Kết quả | Yêu cầu |
|---|---|---|
| Trace lỗi trong 700 trial gài bug | 180 | Chỉ tính trial thực sự kích hoạt lỗi |
| Phát hiện bằng 5 grader, không tính TrialPass | 160/180 = 88.89% | ≥80%, PASS |
| Báo nhầm trên fixed | 0/70 = 0% | ≤10%, PASS |
| misreport | 10/10 trace lỗi được bắt | FM-08 hoạt động |
| Test hai grader và metric FM-08 | 18 passed | PASS |
| Bộ student lab9, bỏ advanced | 29 passed, 317 deselected | PASS |
| evalset --check | 0 problem(s) | PASS |

Các tỷ lệ ngưỡng áp dụng cho toàn ma trận. Riêng `round_down` bắt 20/35 ca lỗi và `pre_deducted` bắt 10/15 ca lỗi. Tổng 20 ca bị bỏ lọt có proposal sai theo nhãn, trong khi các điều kiện ledger, reply, secret, approval và DB đang kiểm vẫn đạt. Những ca này được grader Lab 8 phát hiện qua `proposal_mismatch`. Việc thêm assertion proposal là hướng cải thiện tiếp theo khi cần tăng độ phủ từng cơ chế.

Qua entry point `lab9.eval`, `reports/eval_fixed.json` có `reply_amount_matches_ledger=1.0`. `reports/eval_m3_misreport.json` có `pass_rate=1.0`, `refund_amount_correct=1.0` nhưng `reply_amount_matches_ledger=0.8571`, thấp hơn sàn 0.95. Cả hai report có 70 dòng, cùng eval set và metric spec, không có evaluator failure. Điều này xác nhận metric mới phát hiện phần sai tiền trong lời trả lời mà grader outcome cũ bỏ lọt.

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
