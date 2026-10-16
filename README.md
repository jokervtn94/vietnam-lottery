# Vietnam Lottery Data Fetcher — Maintained Edition


Công cụ tự động thu thập, xử lý và lưu trữ dữ liệu xổ số từ ba miền của Việt Nam (Bắc, Trung, Nam).

## Tính năng

- Thu thập kết quả xổ số Miền Bắc (XSMB), Miền Nam (XSMN) và Miền Trung (XSMT).
- Tự động điều chỉnh ngày thu thập dựa trên múi giờ Việt Nam để đảm bảo dữ liệu đầy đủ.
- Lưu trữ dữ liệu dưới nhiều định dạng:
  - Dữ liệu thô (raw data) dưới dạng JSON và CSV/Parquet.
  - Dữ liệu 2 số cuối (2-digits data) dưới dạng CSV/Parquet, phục vụ phân tích.
  - Dữ liệu dạng ma trận thưa (sparse data) dưới dạng CSV/Parquet, tối ưu cho các phân tích chuyên sâu.
- Hỗ trợ thu thập dữ liệu theo khoảng thời gian tùy chỉnh.

- Tự động cập nhật dữ liệu hàng ngày thông qua GitHub Actions.

## Yêu cầu hệ thống

- Python 3.13 trở lên
- Các thư viện Python được liệt kê trong `requirements.txt`

## Cài đặt

1. Clone repository này về máy:

```bash
git clone https://github.com/jokervtn94/vietnam-lottery.git
cd vietnam-lottery
```

2. Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

## Cách sử dụng

Dự án này cung cấp hai script chính để bạn tương tác: `fetch.py` để thu thập dữ liệu và `lottery_analyzer.py` để thống kê mô tả kết quả lịch sử (không phải mô hình dự đoán).

### 1. Thu thập dữ liệu (Bắt buộc)

Đây là bước đầu tiên và quan trọng nhất. Bạn cần thu thập dữ liệu xổ số trước khi có thể thực hiện bất kỳ phân tích nào.

- **Chạy từ dòng lệnh:**
  Script `src/fetch.py` cho phép thu thập dữ liệu từ cả ba miền.
  - Để thu thập dữ liệu cho ngày hiện tại (hoặc ngày gần nhất có kết quả):
    ```bash
    python -m src.fetch
    ```
  - Để thu thập dữ liệu đến một ngày cụ thể:
    ```bash
    python -m src.fetch --end YYYY-MM-DD
    ```
    Nếu không cung cấp ngày bắt đầu (`--start`), script sẽ tự động xác định ngày bắt đầu:
    - Nếu đã có dữ liệu, script sẽ bắt đầu thu thập từ ngày tiếp theo của ngày cuối cùng trong dữ liệu hiện có.
    - Nếu chưa có dữ liệu, script sẽ thu thập dữ liệu của 7 ngày gần nhất tính từ ngày kết thúc.

    Ví dụ:
    ```bash
    python -m src.fetch --end 2023-12-31
    ```
    Script sẽ tự động lưu dữ liệu vào thư mục `data/` dưới nhiều định dạng khác nhau (JSON, Parquet, CSV).

### 2. Phân tích kết quả lịch sử

Sau khi đã có dữ liệu, bạn có thể chạy script `lottery_analyzer.py` để tạo các biểu đồ phân tích tần suất và dự đoán bằng Machine Learning.

- **Chạy từ dòng lệnh:**
  ```bash
  python -m src.lottery_analyzer
  ```
- **Kết quả:**
  Script này sẽ:
  1. Đọc dữ liệu từ các file `*-2-digits.csv` trong thư mục `data/`.
  2. Thực hiện thống kê tần suất, số kỳ có mặt và thời gian chưa xuất hiện. Không huấn luyện mô hình ML.
  3. Lưu các biểu đồ phân tích và dự đoán (dưới dạng file `.png`) vào thư mục `data/`. Các biểu đồ này chính là những hình ảnh bạn thấy trong phần "Phân tích và Dự đoán Kết quả" của file README này.

## Cấu trúc dự án

```
vietnam-lottery/
├── .github/                  # Cấu hình GitHub Actions
│   └── workflows/
│       └── update-data.yml   # Workflow tự động cập nhật dữ liệu
├── data/                     # Thư mục chứa dữ liệu xổ số đã thu thập
│   └── analysis/             # (Có thể chứa các script hoặc kết quả phân tích)
├── requirements.txt          # Các thư viện Python cần thiết
├── src/
│   ├── fetch.py              # Script chính để thu thập dữ liệu
│   ├── lottery_analyzer.py   # Script phân tích tần suất và dự đoán kết quả
│   ├── lottery_base.py       # Lớp cơ sở trừu tượng cho các loại xổ số
│   ├── lotterymb.py          # Module xử lý xổ số Miền Bắc
│   ├── lotterymn.py          # Module xử lý xổ số Miền Nam
│   ├── lotterymt.py          # Module xử lý xổ số Miền Trung
│   └── models/               # Định nghĩa các Pydantic model cho dữ liệu
│       ├── lottery_mb.py
│       ├── lottery_mn.py
│       └── lottery_mt.py
└── README.md                 # File hướng dẫn sử dụng dự án
```

## Thư viện sử dụng

- `beautifulsoup4`: Phân tích cú pháp HTML từ các trang web.
- `cloudscraper`: Xử lý các biện pháp bảo vệ website (như Cloudflare) để thu thập dữ liệu.
- `numpy`: Hỗ trợ các phép toán số học hiệu quả.
- `pandas`: Xử lý, phân tích và lưu trữ dữ liệu dưới dạng DataFrame.
- `pydantic`: Kiểm tra và xác thực dữ liệu, đảm bảo tính toàn vẹn của dữ liệu xổ số.
- `requests`: Thực hiện các yêu cầu HTTP (được sử dụng bởi `cloudscraper`).
- `lxml`: Bộ phân tích cú pháp HTML/XML nhanh chóng (được được sử dụng bởi `beautifulsoup4`).
- `matplotlib`: Thư viện để tạo biểu đồ và trực quan hóa dữ liệu.
- `scikit-learn`: Thư viện cho các thuật toán học máy, được sử dụng để xây dựng mô hình dự đoán.

## Tự động cập nhật dữ liệu

Dự án này tích hợp GitHub Actions để tự động thu thập và cập nhật dữ liệu xổ số hàng ngày.

- **Lịch trình:** Workflow `update-data.yml` đặt lịch chính 18:45 (giờ Việt Nam).
- **Kích hoạt thủ công:** Bạn cũng có thể kích hoạt workflow này thủ công thông qua giao diện GitHub Actions.
- **Cách hoạt động:** Workflow sẽ checkout mã nguồn, cài đặt các thư viện, chạy script `src/fetch.py` để thu thập dữ liệu mới nhất, sau đó commit và push các thay đổi dữ liệu trở lại repository.

## Đóng góp

Mọi đóng góp đều được hoan nghênh. Vui lòng tạo issue hoặc pull request nếu bạn muốn cải thiện dự án.

## License

[Thêm thông tin về license của dự án]

## Phân tích Kết quả

Phần này cung cấp các phân tích về những con số xuất hiện thường xuyên nhất và những con số đã lâu không xuất hiện.

### Các số xuất hiện nhiều nhất theo từng vùng miền
Biểu đồ theo miền (được tạo bởi GitHub Actions): ![MB](data/mb-most-frequent.png) · ![MN](data/mn-most-frequent.png) · ![MT](data/mt-most-frequent.png)

### Các số lâu rồi không xuất hiện theo từng vùng miền
Biểu đồ theo miền (được tạo bởi GitHub Actions): ![MB](data/mb-least-recent.png) · ![MN](data/mn-least-recent.png) · ![MT](data/mt-least-recent.png)

### Tình trạng dữ liệu gốc

- Sao chép nguyên bản CSV và JSON của ba miền, không tự động sửa các bản ghi cũ.
- Lỗi cũ XSMB gán nhầm `prize3_5` từ `prize3_3` cần thu thập lại **có đối chứng**; hiện tại chỉ sửa luồng thu thập mới.
- Ngày không có kết quả có thể là ngày nghỉ quay (ví dụ lịch Tết), không mặc định là lỗi nguồn.
- Tệp Parquet/PNG là **dữ liệu dẫn xuất**, tạo lại bởi workflow `Rebuild derived Parquet and charts` hoặc lệnh trên, không phải nguồn xác minh kết quả.
- Để đồng bộ Apps Script, ưu tiên dùng `data/xsmn-2-digits.csv`, `data/xsmt-2-digits.csv`, `data/xsmb-2-digits.csv`, kiểm tra trạng thái chất lượng nguồn và thời điểm cập nhật.

## Tự động cập nhật kết quả hằng ngày

GitHub Actions đặt lịch chính 18:45 (giờ Việt Nam). Do lịch `schedule` có thể trễ, mỗi lần chạy kiểm tra cả ba miền nhưng chỉ lấy đến ngày đã qua mốc công bố của miền tương ứng; không tải kết quả chưa quay khi cron chạy qua nửa đêm. Các mốc là **dự kiến**, không bảo đảm khởi chạy đúng phút. Dữ liệu hợp lệ được lưu vào `data/` trên nhánh `main` dưới dạng CSV/JSON/Parquet và thống kê mô tả.

**Chi tiết:** [Lịch và quy trình tự động lưu kết quả](docs/AUTO_UPDATE.md). Các ngày nguồn lỗi không tự biến thành số 00; nếu tải được một phần, kết quả hợp lệ vẫn được lưu và workflow báo cảnh báo lỗi ở cuối.
