# Vietnam Lottery — ghi chú sửa lỗi và triển khai (14/10/2026)

**Nguồn:** [aloha123890/vietnam-lottery](https://github.com/aloha123890/vietnam-lottery), commit `0e252a294eb835494a7beda489545ca60c1f2f9f`. Bản này được đưa vào repository của Jokervtn94 để bảo trì và kiểm chứng.

## Những lỗi đã sửa

| Mã nguồn | Thay đổi |
| --- | --- |
| `src/lotterymb.py` | Sửa `prize3_5` lấy đúng giá trị giải ba thứ năm thay vì `prize3_3`; từ chối dữ liệu rỗng hoặc thiếu trường |
| `src/lottery_base.py` | Đọc nội dung nhiều phần tử HTML có ngăn cách; từ chối placeholder, ô trắng, không lặng lẽ thay bằng số 00 |
| `src/lotterymn.py`, `src/lotterymt.py` | Bắt buộc xác thực cơ cấu giải trước khi lưu model |
| `src/fetch.py` | Đồng bộ mỗi miền từ lịch riêng; `--repair-gaps`; `--force` cần ngày bắt đầu/kết thúc cụ thể; khôi phục dữ liệu cũ nếu re-fetch thất bại |
| `src/data_quality.py` | Kiểm tra ngày, đài, trùng dòng, các cột giải, phạm vi 00–99, đối chiếu CSV gốc và 2-digit, cảnh báo lịch sử XSMB |
| `src/lottery_analyzer.py` | Phân biệt số lượt xuất hiện và số kỳ/đài có xuất hiện; hỗ trợ `--as-of`; thống kê mô tả, không phải ML dự đoán |
| `tests/*.py` | Thêm kiểm thử HTML parser giả lập, số 00, lịch từng miền và các lỗi chất lượng |
| `.github/workflows/tests.yml` | Chạy kiểm thử tự động trên push và PR |
| `.github/workflows/update-data.yml` | Lịch 16:45, 17:45, 18:45 Việt Nam; token mặc định; chống chạy trùng; chỉ commit khi thay đổi dữ liệu |
| `.github/workflows/rebuild-artifacts.yml`, `tools/rebuild_artifacts.py` | Sinh lại Parquet và PNG từ CSV hiện có sau khi nhập `main` |

## Quy tắc quản trị dữ liệu lịch sử

- Sao chép nguyên bản các tệp CSV và JSON của XSMB, XSMN, XSMT từ upstream; giữ SHA nội dung khi chuyển GitHub.
- Trường `prize3_3` và `prize3_5` của XSMB cũ bị trùng đáng ngờ do mã gốc. Sửa parser không khôi phục được số giải cũ, muốn sửa phải đối chiếu nguồn theo từng ngày.
- Khoảng 16–19/02/2026 cần xác minh lịch nghỉ quay dịp Tết trước khi đánh dấu là thiếu kết quả.
- Không coi số 00 là thiếu dữ liệu; ô thiếu/null và 00 hợp lệ phải phân biệt.
- Dữ liệu một đài/ngày của MN/MT không được trộn với dữ liệu một ngày XSMB khi so sánh tỷ lệ xuất hiện.
- Không coi tần suất cao hoặc lâu chưa xuất hiện là xác suất trúng số tăng ở kỳ tiếp theo.

## Cách chạy

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.data_quality
python -m src.data_quality --strict
python -m src.lottery_analyzer --region MN --as-of 2026-10-13
python tools/rebuild_artifacts.py
python -m src.fetch --region MN
python -m src.fetch --region MB --start 2026-10-13 --end 2026-10-13 --force
```

## Phát hành

1. Nhập nhánh sửa vào `main` sau khi kiểm tra kết quả workflow `Quality checks`.
2. `Rebuild derived Parquet and charts` tạo lại các file Parquet/PNG mà giao diện kết nối GitHub không sao chép dạng binary nguyên gốc được.
3. `Update Vietnam Lottery Data` được lên lịch mỗi ngày cho ba miền; cần quan sát log vì lịch có thể trễ, và lỗi nguồn web vẫn có thể xảy ra.
4. Báo cáo thống kê chỉ là bằng chứng lịch sử; chưa triển khai Apps Script và không được dùng làm chứng cứ khoa học cho việc luận Tứ Trụ.

## Ghi công và giấy phép

Phiên bản nguồn do [aloha123890](https://github.com/aloha123890/vietnam-lottery) cung cấp. README nguồn chưa có văn bản LICENSE hoàn chỉnh. GitHub công khai không tự động cấp quyền tái phân phối; cần xác nhận điều kiện sử dụng với chủ sở hữu nguồn khi phát hành rộng rãi.

## Giới hạn xác thực

Chưa chạy end-to-end scraper trực tuyến sau thay đổi; xác nhận tích hợp phải dựa vào GitHub Actions và so sánh lại một số kỳ quay với trang kết quả.
