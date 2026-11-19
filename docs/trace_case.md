# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

## Mẫu điền

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11` |
| Triệu chứng | Grader `pass_rate`, `refund_amount_correct`, `db_fact_kept` đều FAIL. Status trả về `resolved` trong khi kỳ vọng `denied`. Ledger ghi nhận hoàn 20.000đ (`refund_count=1`) trong khi kỳ vọng 0đ. Reply thông báo: *"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."* |
| Bước sai đầu tiên | Event 3: `model_override` payload: `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event 1 (`handoff`) và Event 2 (`investigator`) hoàn toàn đúng: tra cứu DB đơn hàng O-202 trả về `delay_days=0`. Đến Event 3, agent tự ý tin số ngày trễ người dùng khai trong ticket và gài override `delay_days: 5`. Các bước tiếp theo (Event 4 `quote` 20.000đ, hoàn tiền vào ledger) đều sai do hệ quả trực tiếp từ Event 3. |
| Failure mode | `FM-03` (`ticket_trust` — tin ticket hơn DB) |
| Đối chứng | Cùng claim `C-002@11` trên shape `fixed`: Hoàn toàn không có Event `model_override`. Event 3 là `quote` trả về `amount_vnd: 0, reason: no_entitlement`, kết quả status `denied`, ledger=0đ. |
| Regression test | Grader `DbFactKept` và `RefundAmountCorrect` (trong `src/lab9/graders.py` và `tests/test_lab9_graders.py::test_override_event_breaks_db_fact`). Đã xác nhận FAIL trên `seeded_regression` và PASS trên `fixed`. |
| Chưa chắc chắn | Trace chỉ ghi nhận hành vi `model_override` nhưng không ghi nhận suy luận nội tâm (Chain-of-Thought) của LLM về lý do tại sao lại ưu tiên độ tin cậy của ticket hơn dữ liệu gốc từ DB. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
