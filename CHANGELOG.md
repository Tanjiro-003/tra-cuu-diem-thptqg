# Changelog

## 2.0.0

- ⚡ Thêm tra cứu **đa luồng** cho chế độ hàng loạt (`--workers`), mỗi luồng dùng session riêng.
- 📈 Nâng cấp phổ điểm: biểu đồ histogram theo mốc 0.5 điểm + bảng thống kê (ĐTB, trung vị, ĐLC, MAD, tỉ lệ <5/≥7/≤1, mode, điểm 10/0), lưu theo thư mục từng môn.
- 📅 Xuất Excel và biểu đồ theo năm (`--year`, mặc định là năm hiện tại).
- 🎨 Thêm module `ui.py`: banner, thanh tiến độ, bảng điểm có màu cho dễ theo dõi.
- 🧹 File Captcha nhập tay đặt tên theo SBD (`captcha_<sbd>.png`) để chạy song song không đè lên nhau, tự xoá sau khi tra cứu xong.
- 🔁 Giới hạn số lần thử lại Captcha (`MAX_CAPTCHA_RETRIES`) để tránh treo vô hạn khi Captcha luôn sai.

## 1.0.0

- Phiên bản đầu tiên: tách code gốc thành các module (`config`, `captcha`, `api`, `parser`, `report`, `cli`).
- Tra cứu 1 SBD hoặc hàng loạt (tuần tự) từ `sbd.txt`.
- Giải Captcha qua 2Captcha hoặc nhập tay.
- Xuất Excel và vẽ histogram phổ điểm cơ bản cho từng môn.
- Có unit test cho phần phân tích chuỗi điểm.
