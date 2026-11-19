# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt (κ=0.757 ≥ 0.6, P=0.857 ≥ 0.8, R=0.800 ≥ 0.7) | dùng |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không đạt (κ=0.375 < 0.6, R=0.300 < 0.7) | loại |

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú & Hành động sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 | PASS | FAIL | Người đúng | Reply: *"Em đã hoàn tiền cho anh rồi nha, anh check giúp em."* Người bắt lỗi xưng hô "anh - em" suồng sã, thiếu văn phong chuyên nghiệp chuẩn mực của CSKH LogiX. Judge bỏ qua vì thấy câu văn thân thiện. **Sửa rubric:** Cấm xưng hô suồng sã cá nhân ("anh - em", "bạn ơi"), bắt buộc ngôi xưng chuẩn "LogiX - Quý khách/Anh/Chị". |
| 2 | H-017 | PASS | FAIL | Người đúng | Reply: *"Dạ, bạn ơi LogiX đã hoàn 25.000đ cho đơn O-606 rồi nha."* Người bắt lỗi dùng khẩu ngữ "bạn ơi", "nha". Judge bỏ sót. **Sửa rubric:** Bổ sung danh sách khẩu ngữ không phù hợp vào prompt của Judge. |
| 3 | H-029 | PASS | FAIL | Người đúng | Reply: *"Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm."* Người bắt lỗi câu "không cần nhắn thêm" mang sắc thái cộc lốc, gắt gỏng, từ chối hỗ trợ. Judge bỏ sót. **Sửa rubric:** Định nghĩa rõ lỗi cộc lốc / đuổi khách là vi phạm nghiêm trọng (FAIL). |
| 4 | H-042 | FAIL | PASS | Người đúng | Reply: *"Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ."* Judge phạt vì hẹn mốc thời gian 3–5 ngày. Người coi đây là thông tin chuẩn mực và lịch sự. **Sửa rubric:** Hướng dẫn Judge rằng thông báo thời gian đối soát ngân hàng là hợp lệ, không tính là lỗi tone. |
| 5 | H-051 | FAIL | PASS | Người đúng | Reply: *"Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ."* Judge phạt vì dùng từ mượn tiếng Anh "refund". Người chấp nhận vì đây là thuật ngữ e-commerce quen thuộc. **Sửa rubric:** Cho phép các thuật ngữ dịch vụ phổ thông trừ khi có quy định thuần Việt bắt buộc. |
| 6 | HL-016 | PASS | FAIL | Người đúng | Reply: *"Dạ, LogiX thành thật xin lỗi anh/chị vì sự bất tiện này..."* (judge_helpful). Câu trả lời chỉ xin lỗi suông nhưng hoàn toàn không giải quyết được claim của khách. Judge nhầm lẫn giữa lịch sự và hữu ích, dẫn đến Recall chỉ đạt 30% (bỏ sót 21/30 ca lỗi). |

## Kết luận
- **Tiêu chí bị loại và lý do:** `helpful` bị loại hoàn toàn khỏi CI Gate vì $\kappa = 0.375 < 0.6$ và $\text{Recall} = 0.300 < 0.7$. Ma trận nhầm lẫn cho thấy $\text{fn} = 21$ trên tổng số 30 ca lỗi (tỷ lệ bỏ sót lỗi tới 70%). Judge này có xu hướng thiên vị nhãn PASS mỗi khi agent xin lỗi lịch sự, không có năng lực đánh giá tính hữu ích thực sự.
- **Tiêu chí được chấp nhận:** `tone_ok` đạt chuẩn sàn ($\kappa = 0.757 \ge 0.6$, $\text{Precision} = 0.857 \ge 0.8$, $\text{Recall} = 0.800 \ge 0.7$), tỷ lệ lỗi quan sát 28% tương ứng tỷ lệ lỗi hiệu chỉnh Rogan-Gladen là 30%. Có thể sử dụng làm gate theo dõi hoặc phi chặn.
- **Rủi ro còn lại:** Judge mới chỉ được kiểm định trên tập replay tĩnh đã công khai (`judge_tone_public.csv`). Khi phân phối prompt hoặc câu trả lời của agent thay đổi trong môi trường thực tế, cần thu thập mẫu mới được dán nhãn thủ công (held-out validation set) để tái hiệu chuẩn.
