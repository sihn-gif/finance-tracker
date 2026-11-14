# Personal Finance Tracker (Nhóm 3 – Mini-project 1.1)

Ứng dụng web ghi thu/chi, đặt ngân sách theo tháng, cảnh báo khi gần vượt và xem biểu đồ theo danh mục.

**Nhóm:** Huỳnh Hồng Nhung · Trần Tố Uyên · Nguyễn Trung Sinh
**Công nghệ:** Python 3.11+, Flask, SQLite (Flask-SQLAlchemy), Chart.js, pytest

## Cài đặt và chạy (làm lần lượt)

```bash
git clone <link-repo>
cd finance-tracker

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
python seed.py                 # (tuỳ chọn) tạo dữ liệu mẫu
python run.py                  # mở http://127.0.0.1:5000
```

Chạy test: `pytest`

## Cấu trúc thư mục

| Đường dẫn | Dùng để làm gì |
|---|---|
| `app/models.py` | Bảng dữ liệu: Category, Transaction, Budget |
| `app/services.py` | Logic nghiệp vụ + kiểm tra dữ liệu (nơi viết test) |
| `app/routes.py` | Các đường dẫn web (nhận form, gọi services) |
| `app/templates/index.html` | Giao diện (Nhung chỉnh ở đây) |
| `tests/test_services.py` | Unit test (Uyên mở rộng ở đây) |
| `seed.py` | Tạo dữ liệu mẫu |

## Đã có sẵn
- Thêm, xem, xóa giao dịch (có kiểm tra: số tiền > 0, ngày hợp lệ, danh mục tồn tại)
- Đặt ngân sách theo tháng/danh mục (không trùng), cảnh báo ở 80% và 100%
- Tổng thu/chi/còn lại theo tháng, biểu đồ chi tiêu theo danh mục
- Bộ unit test ban đầu

## Việc còn lại (mỗi việc tạo thành 1 Issue)
| Việc | Gợi ý người làm |
|---|---|
| Sửa giao dịch (Update trong CRUD): route `/transactions/<id>/edit` + form + hàm `update_transaction` trong services | Sinh hướng dẫn, Uyên làm |
| Trang báo cáo tháng riêng (bảng tổng hợp thu/chi theo danh mục, so với tháng trước) | Nhung |
| Cải thiện giao diện, thử trên điện thoại, usability testing 2–3 người | Nhung |
| Xuất CSV giao dịch trong tháng | Uyên |
| Thêm test: sửa giao dịch, xuất CSV, các trường hợp biên mới | Uyên |
| Bảng test case + khung báo cáo (dưới 10 trang A4) | Uyên |
| Quản lý danh mục (thêm/xóa, không cho xóa danh mục đang có giao dịch) | Sinh |
| Deploy (PythonAnywhere hoặc Render) | Sinh |

## Quy tắc làm việc nhóm
- Không code trực tiếp trên `main`. Tạo nhánh `feature/ten-viec`, xong thì mở Pull Request, Sinh review rồi merge.
- Commit nhỏ, message rõ ràng (ví dụ: `Add budget warning at 80%`).
- Trước khi mở Pull Request: chạy `pytest` phải xanh hết.
