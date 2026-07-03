# 🎯 Phổ Điểm Radar

**Tra cứu điểm thi tốt nghiệp THPT tự động, đa luồng, kèm giải Captcha và phổ điểm chuyên sâu — chỉ trong vài dòng lệnh.**

> Công cụ tự động lấy điểm thi tốt nghiệp THPT từ cổng tra cứu chính thức, hỗ trợ giải Captcha qua [2Captcha](https://2captcha.com) (hoặc nhập tay), tra cứu **đa luồng** cho danh sách lớn, tự động thử lại khi Captcha sai, xuất kết quả ra Excel và vẽ **biểu đồ phổ điểm chuyên sâu kèm bảng thống kê** (ĐTB, trung vị, độ lệch chuẩn, tỉ lệ điểm liệt, mode...) cho từng môn.

---

## ✨ Tính năng

- 🔍 **Tra cứu 1 SBD hoặc hàng loạt** từ file `sbd.txt`
- ⚡ **Đa luồng** khi tra cứu hàng loạt (khi dùng 2Captcha) — mỗi luồng có session riêng, không đè token Captcha của nhau
- 🤖 **Tự động giải Captcha** qua 2Captcha, hoặc rơi về nhập tay nếu chưa cấu hình / hết tiền (mỗi SBD một file Captcha riêng, an toàn khi chạy song song)
- 🔁 **Tự thử lại** khi Captcha sai, có giới hạn số lần để tránh vòng lặp vô hạn
- 📊 **Xuất Excel** theo năm (`KetQua_DiemThi_<năm>.xlsx`)
- 📈 **Phổ điểm chuyên sâu**: biểu đồ histogram theo từng mốc 0.5 điểm + bảng thống kê (Số TS, ĐTB, Trung vị, ĐLC, MAD, tỉ lệ <5, ≥7, ≤1, Mode, số điểm 10/0), lưu theo thư mục từng môn trong `PhoDiem/<Môn>/PhoDiem_<năm>.png`
- 🎨 **Giao diện dòng lệnh có màu**: banner, thanh tiến độ, bảng điểm — dễ nhìn, dễ theo dõi tiến trình
- 🧱 Code tổ chức thành module rõ ràng, dễ đọc, dễ mở rộng
- ✅ Có sẵn unit test cho phần phân tích chuỗi điểm

## 📦 Cấu trúc dự án

```
pho-diem-radar/
├── main.py                        # Entrypoint chạy nhanh
├── requirements.txt
├── config_2captcha.example.json   # Mẫu cấu hình (copy thành config_2captcha.json)
├── src/score_lookup/
│   ├── ui.py                      # Giao diện dòng lệnh có màu (banner, progress bar, bảng điểm)
│   ├── config.py                  # Đọc/tạo cấu hình, kiểm tra số dư 2Captcha
│   ├── captcha.py                 # Giải Captcha (2Captcha hoặc nhập tay)
│   ├── api.py                     # Giao tiếp API tra cứu điểm + worker đa luồng
│   ├── parser.py                  # Phân tích chuỗi điểm -> dict
│   ├── report.py                  # Xuất Excel + vẽ phổ điểm chuyên sâu
│   └── cli.py                     # Giao diện dòng lệnh
└── tests/
    └── test_parser.py
```

## 🚀 Cài đặt

```bash
git clone https://github.com/<your-username>/pho-diem-radar.git
cd pho-diem-radar
pip install -r requirements.txt
cp config_2captcha.example.json config_2captcha.json
```

Nếu muốn tự động giải Captcha (và mở khoá chế độ đa luồng), điền `api_key` của bạn vào `config_2captcha.json` và đặt `"enable": true`. Không có key cũng chạy được — công cụ sẽ yêu cầu bạn nhập Captcha thủ công, khi đó số luồng tự động về 1 để tránh rối console.

## 🖥️ Sử dụng

**Chế độ tương tác** (hỏi lựa chọn, hỏi số luồng nếu có 2Captcha):

```bash
python main.py
```

**Tra cứu 1 số báo danh:**

```bash
python main.py --sbd 01000123
```

**Tra cứu hàng loạt, đa luồng** — tạo file `sbd.txt` (mỗi SBD một dòng), rồi chạy:

```bash
python main.py --batch --batch-file sbd.txt --workers 8 --year 2026
```

Cờ `--year` dùng để đặt tên file Excel/biểu đồ (mặc định lấy năm hiện tại). `--workers` chỉ có tác dụng khi đã bật 2Captcha.

## 🧪 Chạy test

```bash
pytest
```

## ⚠️ Lưu ý sử dụng

- Công cụ này tương tác với cổng tra cứu điểm thi công khai; hãy tự chịu trách nhiệm tuân thủ điều khoản sử dụng của trang và chỉ tra cứu SBD mà bạn có quyền truy cập hợp pháp (của bản thân, con em, hoặc học sinh mình phụ trách).
- Khi chạy đa luồng, cân nhắc số luồng hợp lý để tránh gây quá tải hệ thống tra cứu điểm.
- File `config_2captcha.json` chứa API key cá nhân — **không commit** file này lên GitHub (đã có sẵn trong `.gitignore`).

## 📄 License

[MIT](LICENSE)

---

Nếu thấy hữu ích, đừng ngại thả ⭐ cho repo nhé!
