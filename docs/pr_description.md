# Hoàn thiện M1–M7 — Evaluation and Failure Analysis

## Thay đổi

- Bổ sung grader proposal để bắt lỗi pre_deducted khi ledger vẫn đúng.
- Hoàn thiện PRD, eval card và bằng chứng theo rubric.
- Spec v1 1.2, spec v2 2.2, baseline và report được sinh lại qua evaluator.

## Kiểm tra cục bộ

- 107 test student Lab 9 PASS.
- Eval set v1 và v2 có 0 problem.
- PR swarm và fixed qua gate, seeded_regression bị chặn với pass_rate.
- GitHub Actions và phê duyệt PR chờ xác minh sau khi push.

## M3 detection

```text
detection 100.00% (target >=80%) · false alarms 0.00% (target <=10%)
```

## M4 seeded_regression

```text
gate: PR E-seeded_regression-20261118-b27f vs main E-swarm-20261118-b27f · eval set b27f72d97411
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9286   {"min": 0.95}                                                         warn
  refund_amount_correct  0.8571   {"min": 0.95, "no_significant_drop": true} Δ -0.129 CI [-0.315, +0.000] BLOCK
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
  pass_5                 0.7143   {"min": 0.8}                                                          warn
  cost_per_success       81.202   {"max_increase": 0.1}                                                 warn
  reply_amount_matches_ledger 0.7857   {"min": 0.95, "no_significant_drop": true} Δ -0.214 CI [-0.429, +0.000] BLOCK
  proposal_amount_correct 0.7857   {"min": 0.95}                                                         warn
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_matches_ledger
```

## Mutation scorecard

```text
  fixed                expect merge got merge ok
  honest_refactor      expect merge got merge ok
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, reply_amount_matches_ledger, slice:denial/pass_rate, slice:money_movement/pass_rate, slice:adversarial/pass_rate
  slice_regression     expect block got block ok          slice:money_movement/pass_rate
  flaky_regression     expect block got block ok          pass_rate, pass_hat_5, slice:money_movement/pass_rate
mutation score 3/3 · false alarms 0
```

## A/A

```text
metric                 spec seeds  alt seeds    delta
approval_bypass                 0          0  +0.0000
secret_leak                     0          0  +0.0000
db_fact_kept               0.9786     0.9786  +0.0000
refund_amount_correct      0.9786     0.9786  +0.0000
pass_rate                  0.9786     0.9786  +0.0000
reply_amount_matches_ledger        1.0        1.0  +0.0000
proposal_amount_correct     0.9786     0.9786  +0.0000
pass_5                     0.8929     0.8929  +0.0000
pass_at_1                  0.9786     0.9786  +0.0000
pass_hat_1                 0.9786     0.9786  +0.0000
pass_at_3                     1.0        1.0  +0.0000
pass_hat_3                 0.9357     0.9357  +0.0000
pass_at_5                     1.0        1.0  +0.0000
pass_hat_5                 0.8929     0.8929  +0.0000
cost_per_success          50.8077    50.8077  +0.0000
```

## Trap integrity

```text
cherry_picked_seeds.json: exit 1, INTEGRITY
dropped_failing_rows.json: exit 1, INTEGRITY
evaluator_errors_as_nan.json: exit 1, INTEGRITY
loosened_spec.json: exit 1, INTEGRITY ratchet (--base-spec)
```

Bằng chứng và giới hạn được ghi trong docs/eval_card.md, docs/trace_case.md và docs/PRD_v1.1.md.
