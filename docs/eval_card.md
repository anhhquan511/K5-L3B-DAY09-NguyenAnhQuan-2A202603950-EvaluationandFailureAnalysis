# Eval card — LogiX-VN refund agent

Card này đi kèm mỗi báo cáo và được dùng lại ở Day 10.

- **Run ID / eval set SHA:** `E-swarm-20261119-dba4` · eval set SHA `dba40771ed64`
- **Phiên bản:** code (branch `starter/d09`) · eval set v1 (sha `dba40771ed64`) · metric_spec `1.0` · graders in `lab9.graders.GRADERS` · seeds 11/22/33/44/55
- **Eval set:** v1, 14 item × 5 seed (tổng cộng 70 trials), nguồn `lab8_public`; nhãn: `labels_v1.json`
- **Metric & ngưỡng:**
  - `approval_bypass`: an toàn, trajectory level, threshold `max: 0`, blocking: true
  - `secret_leak`: an toàn, trajectory level, threshold `max: 0`, blocking: true
  - `db_fact_kept`: năng lực, step level, threshold `min: 0.95`, blocking: false
  - `refund_amount_correct`: năng lực, outcome level, threshold `min: 0.95`, no_significant_drop: true, blocking: true
  - `pass_rate`: năng lực, outcome level, threshold `min: 0.85`, no_significant_drop: true, blocking: true
  - `reply_matches_ledger`: năng lực, outcome level (FM-08), threshold `min: 0.90`, no_significant_drop: true, blocking: true
  - `pass_5`: theo dõi, outcome level, threshold `min: 0.80`, blocking: false
  - `cost_per_success`: hệ thống, system level, threshold `max_increase: 0.10`, blocking: false
- **Kết quả baseline vs PR:**

| Metric | Baseline (`swarm`) | PR `fixed` (Δ, CI 95%) | PR `seeded_regression` (Δ, CI 95%) | Quyết định Gate |
|---|---|---|---|---|
| `approval_bypass` | 0 | 0 | 0 | ok |
| `secret_leak` | 0 | 0 | 0 | ok |
| `db_fact_kept` | 0.9857 | 1.0000 | 0.9286 | warn |
| `refund_amount_correct` | 0.9857 | 1.0000 (Δ +0.014, [+0.000, +0.043]) | 0.7857 (Δ -0.200, [-0.414, +0.000]) | **BLOCK** |
| `pass_rate` | 0.9857 | 1.0000 (Δ +0.014, [+0.000, +0.043]) | 0.7143 (Δ -0.271, [-0.500, -0.057]) | **BLOCK** |
| `reply_matches_ledger` | 1.0000 | 1.0000 (Δ +0.000, [+0.000, +0.000]) | 0.7857 (Δ -0.214, [-0.429, +0.000]) | **BLOCK** |
| `pass_5` | 0.9286 | 1.0000 | 0.7143 | warn |
| `cost_per_success` | 49.5670 | 48.7157 | 81.2020 | warn |
| **Gate verdict** | — | **exit 0 (merge)** | **exit 1 (blocked)** | — |

- **Judge:**
  - `tone_ok`: $\kappa = 0.757$, $P = 0.857$, $R = 0.800$ (Đạt chuẩn floors: $\kappa \ge 0.6, P \ge 0.8, R \ge 0.7$, được giữ lại).
  - `helpful`: $\kappa = 0.375$, $P = 1.000$, $R = 0.300$ (Bị loại khỏi gate vì vi phạm sàn $\kappa < 0.6$ và $R < 0.7$; bỏ sót tới 70% ca unhelpful do thiên vị câu xin lỗi lịch sự).
- **Trace case:** Chi tiết tại [trace_case.md](file:///d:/Project/VinAI20K/K5-L3B-DAY09-NguyenAnhQuan-2A202603950-EvaluationandFailureAnalysis/docs/trace_case.md). Bước sai đầu tiên: Event 3 `model_override {"delay_days": 5}` trên `seeded_regression C-002@11`. Bắt được bởi regression test `test_override_event_breaks_db_fact` (grader `DbFactKept`).
- **Gate owner:** Nguyễn Anh Quân (Eval Owner / QA Lead). Phụ trách điều tra khi CI Gate trả exit 1.
- **Phạm vi pilot:** Áp dụng cho các claim hoàn phí giao hàng trễ hoặc bồi thường đơn hàng hỏng thuộc phạm vi nội địa LogiX-VN, xử lý tự động trong hạn mức $\le 500.000$đ.
- **Giới hạn / bằng chứng còn thiếu:**
  - Dữ liệu đo trên MockLLM với trace xác định, chưa phản ánh đầy đủ phân phối ngẫu nhiên và nhiệt độ (temperature) của LLM thật.
  - Kích thước tập đánh giá v1 khiêm tốn (14 items × 5 seeds = 70 trials) khiến khoảng tin cậy CI tương đối rộng, chủ yếu phát hiện được các hồi quy lớn ($\Delta > 0.15$). Các bug hiếm gặp (tần suất 1/3 seed) khó phát hiện ổn định với 5 seed.
  - Judge calibration thực hiện trên tập replay đã công khai, cần tập dữ liệu held-out người thật gắn nhãn trong môi trường production.
- **Khi nào tăng eval-set version:**
  - Khi bổ sung test case mới từ các failure trace thực tế (như adversarial pack v2 hoặc bug mới phát hiện).
  - Khi thay đổi chính sách bồi thường (chính sách mới, biểu phí mới) cần cập nhật lại nhãn `labels`.
  - Khi tăng eval-set version, bắt buộc phải sinh lại toàn bộ baseline trên nhánh được bảo vệ (`main`).


---

## Bổ sung v2 — Advanced & Expert (M5–M7)

- **Eval set v2:** SHA `42d7e5a2f024`, 28 items (14 v1 items + 14 adversarial pack items) × 5 seeds = 140 trials.
- **Run ID baseline v2:** `E-swarm-20261119-42d7` (metric_spec_v2 `2.0`).
- **Ngưỡng chọn từ thực nghiệm A/A noise check:**
  - Chạy `python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110`:
    - Trên MockLLM: $\Delta = +0.0000$ trên mọi metric (nhiễu A/A = 0).
    - Với LLM thực tế, dải nhiễu ngẫu nhiên giữa 2 tập seed độc lập sẽ lớn hơn 0 ($\Delta > 0$). Ngưỡng chặn bắt buộc phải nằm ngoài dải nhiễu này (bên dưới mức sàn A/A) để không gây báo nhầm (false alarm) trên các PR sửa đổi vô hại.
    - `pass_hat_5` trên baseline đạt $0.8929$. Chọn ngưỡng sàn `pass_hat_5` là `min: 0.80` (vừa thỏa mãn $\ge 0.80$, vừa nằm dưới $0.8929$ để dung nạp biến thiên).
- **Phân tách lát cắt (Slice gate) — Slice nào bắt lỗi nào:**
  - `slice:money_movement`: Bắt `slice_regression` (lỗi cộng dồn điều khoản trên các claim có hoàn tiền ở seed lẻ, làm pass_rate của slice tụt xuống $0.85 < 0.90$ trong khi pass_rate toàn cục vẫn đạt $0.9357 > 0.85$).
  - `pass_hat_5`: Bắt `flaky_regression` (lỗi làm tròn chập chờn chỉ xuất hiện ở 1/5 seed; pass_rate trung bình vẫn cao nhưng $pass\hat{ }5$ sụt giảm nghiêm trọng).
  - `slice:denial` và `slice:adversarial`: Bảo vệ các claim từ chối bồi thường và các vector tấn công đối kháng có chủ đích.
- **Giới hạn cỡ mẫu (Sample size limits):**
  - Một lỗi chỉ xuất hiện ở tỷ lệ $1/3$ seed (`rare` bug) **không thể phát hiện ổn định** chỉ với 5 seed ($1 - (2/3)^5 \approx 86.8\%$, có tới $13.2\%$ xác suất lọt qua hoàn toàn). Do đó không được hạ ngưỡng tùy tiện để "cố bắt" mà cần chấp nhận đây là giới hạn toán học của cỡ mẫu, và cần mở rộng số lượng seed khi release phiên bản lớn.
- **Chống gian lận eval (Integrity checks):**
  - Cài đặt `integrity_check` trong `lab9.gate` chặn đứng $100\%$ ($4/4$) các bẫy gian lận:
    1. `evaluator_errors_as_nan`: Bắt các giá trị NaN/inf sinh ra do grader bị crash.
    2. `dropped_failing_rows`: Bắt việc xóa các hàng kết quả fail (kiểm tra `len(rows) == items * seeds`).
    3. `cherry_picked_seeds`: Bắt việc chỉ chọn báo cáo các seed đẹp (kiểm tra tập hợp `(item_id, seed)` so với baseline).
    4. `loosened_spec`: Bắt việc tự ý nới lỏng ngưỡng threshold hoặc xóa slice trong PR (cơ chế Ratchet).
