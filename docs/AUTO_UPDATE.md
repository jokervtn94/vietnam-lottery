# Tự động cập nhật và lưu kết quả xổ số (GitHub Actions)

## Thiết lập hoạt động

Workflow: [Update Vietnam Lottery Data](../.github/workflows/update-data.yml). Kết quả được cập nhật trong nhánh `main`, thư mục `data/`.

| Công việc | UTC (GitHub cron) | Giờ Việt Nam (UTC+7) |
|---|---|---|
| Miền Nam (XSMN) | `45 9 * * *` | 16:45 hằng ngày |
| Thử lại sau XSMN | `25 10 * * *` | 17:25 |
| Miền Trung (XSMT) | `45 10 * * *` | 17:45 |
| Thử lại sau XSMT | `25 11 * * *` | 18:25 |
| Miền Bắc (XSMB) | `45 11 * * *` | 18:45 |
| Thử lại sau XSMB | `25 12 * * *` | 19:25 |
| Đối soát cả ba miền | `15 14 * * *` | 21:15 |
| Đối soát dự phòng | `25 15 * * *` | 22:25 |
| Khôi phục dữ liệu hôm trước | `25 1 * * *` | 08:25 sáng hôm sau |

**Quan trọng:** GitHub Actions `schedule` là lịch dự kiến, **không cam kết khởi chạy đúng phút**, có thể chậm nhiều giờ hoặc bị bỏ qua. Các mốc bổ sung tăng khả năng bắt kịp dữ liệu nhưng không thể bảo đảm thời điểm thực thi. Muốn kích hoạt đúng giờ gần như tuyệt đối cần bộ lập lịch bên ngoài GitHub.

**Khắc phục trường hợp qua nửa đêm:** không dựa duy nhất vào `github.event.schedule` để quyết định miền/ngày tải. Mỗi lần workflow khởi chạy, `TZ=Asia/Ho_Chi_Minh` xác định ngày Việt Nam thực tế và giới hạn `--end` theo từng miền: MN sau 16:45, MT sau 17:45, MB sau 18:45 mới được phép truy vấn kết quả *ngày hiện tại*; trước giờ tương ứng chỉ truy vấn đến *ngày hôm trước*. Do đó cron 21:15 thực thi lúc 01:18 ngày hôm sau sẽ đối soát ngày hôm trước, không tải một kỳ quay chưa diễn ra. Lượt `workflow_dispatch` cũng có quy tắc giới hạn ngày an toàn này.

## Trình tự xử lý

1. GitHub Actions checkout `main` và cài phụ thuộc Python 3.13.
2. Chạy `python -m unittest discover -s tests -v` để loại trừ lỗi hồi quy.
3. Workflow lần lượt gọi `python -m src.fetch --region MN|MT|MB --end YYYY-MM-DD` với mốc `--end` an toàn theo giờ thực tế Việt Nam của **từng miền**; chỉ tải các ngày còn thiếu sau ngày mới nhất đã lưu, không tự tạo số 00.
4. Ghi file JSON nguồn, CSV kết quả gốc, CSV 2 số cuối, CSV/JSON sparse và Parquet của miền có thêm kết quả.
5. Chạy `python -m src.data_quality --output data/data-quality-report.json` để đối chiếu kết quả và số lượng bản ghi.
6. Tạo biểu đồ và `data/analysis-summary.json` bằng `python -m src.lottery_analyzer`.
7. Commit những thay đổi trong `data/` lên `main` bằng `GITHUB_TOKEN`, không ép đẩy (`force push`). Các file không đổi không sinh commit.
8. Nếu một lần tải có lỗi, **các kết quả thành công được commit trước**; workflow vẫn báo thất bại ở bước cuối để có thể xử lý phần thiếu ở lần tiếp theo.

Workflow tái tạo Parquet/PNG và workflow cập nhật sử dụng cùng nhóm khóa tuần tự để tránh đẩy commit đồng thời lên `main`.

## Kiểm tra và chạy thủ công

- Mở tab **Actions → Update Vietnam Lottery Data → Run workflow**, chọn nhánh `main`, bấm **Run workflow**.
- Vào trang run, xem bước **Fetch region for scheduled time**, sau đó kiểm tra **Commit only changed data**.
- Nếu không có số mới hoặc kỳ quay hôm nay chưa đến giờ công bố, dòng `No new data to commit.` là bình thường.
- Xem log `Scheduled cron: ...; Vietnam time: ...` và từng dòng `Fetching ... only through ...` để phân biệt giờ cron dự kiến, giờ thực thi thực tế và ngày kết quả được phép lấy.
- Nếu tải không thành công, run có trạng thái đỏ và ghi các ngày thất bại; dữ liệu đã được lưu trước đó không bị xóa.
- Trong repository, kiểm tra `data/xsmb.json`, `data/xsmn.json`, `data/xsmt.json`, các tệp `*-2-digits.csv` cùng lịch sử commit.
- Xem thêm [data-quality-report.json](../data/data-quality-report.json) và [analysis-summary.json](../data/analysis-summary.json).

## Lưu ý khôi phục và độ chính xác

- Không nạp lại bản lịch sử nếu nguồn JSON đang bị lỗi hoặc parse thất bại; chương trình phải dừng thay vì ghi đè bằng vài ngày dữ liệu.
- Đối với dữ liệu XSMB cũ, lỗi `prize3_5` gán trùng `prize3_3` vẫn cần đối chứng từng kỳ quay. Không tự sửa dữ liệu lịch sử.
- Những ngày không có kỳ quay (ví dụ dịp Tết) có thể gây cảnh báo tải thất bại; không nên tạo giải thưởng giả. Workflow lưu các ngày có dữ liệu thật và báo còn ngày chưa lấy.
- Dữ liệu từ website phụ thuộc vào giao diện công khai và giờ công bố; `success` của GitHub Actions không thay thế việc đối chiếu với nguồn kết quả đáng tin cậy.
- Khi dùng dữ liệu cho Luận Tứ Trụ, xem đây là lớp thống kê/kiểm định độc lập, không phải bằng chứng xác suất dự báo số tài lộc.

## Quyền GitHub

File workflow đặt `permissions: contents: write`. Nếu commit tự động bị từ chối (HTTP 403), vào **Settings → Actions → General → Workflow permissions**, kiểm tra quyền Read and write của token và mọi hạn chế từ chính sách repository.

## Đối chiếu lịch sử cập nhật

Commit mới có dạng `Update lottery data YYYY-MM-DD`. Dữ liệu gốc CSV/JSON được Git quản lý phiên bản; có thể khôi phục commit cũ khi cần. Không tự `force push` nhánh `main`.
