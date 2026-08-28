# 📊 Dự Đoán Chứng Khoán VN

Website tổng hợp dữ liệu phân tích kỹ thuật và dự đoán xu hướng các mã cổ phiếu Việt Nam (HOSE).

## Tính năng

- 📈 Phân tích kỹ thuật tự động cho 15 mã cổ phiếu phổ biến (FPT, VCB, HPG, VNM...)
- 🔢 Các chỉ báo: RSI, MACD, SMA20, EMA20
- 📊 Biểu đồ tròn tỷ lệ MUA/GIỮ/BÁN + biểu đồ cột so sánh tín hiệu
- 🎯 Khuyến nghị tổng hợp: MUA MẠNH / MUA / GIỮ / BÁN / BÁN MẠNH
- 🔄 Cache 5 phút để tối ưu tốc độ
- 📱 Giao diện responsive, hỗ trợ mobile

## Công nghệ

- **Backend:** Python, FastAPI, yfinance, pandas
- **Frontend:** HTML, TailwindCSS, Chart.js
- **Nguồn dữ liệu:** Yahoo Finance

## Chạy local

```bash
pip install -r requirements.txt
python main.py
```

Mở trình duyệt: http://127.0.0.1:8000

## ⚠️ Khuyến cáo

Thông tin trên chỉ mang tính chất tham khảo. Không phải là lời khuyên đầu tư.
