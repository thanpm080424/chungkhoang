from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from scraper import get_stock_predictions, get_market_summary, INTERVAL_LABELS
import os
from datetime import datetime

app = FastAPI(title="Stock Prediction API - Dự đoán Chứng khoán VN")

# Cho phép CORS (hữu ích nếu sau này tách frontend riêng)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup thư mục static cho web HTML/JS
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)


@app.get("/api/predictions")
def get_predictions(interval: str = Query("1_day", description="Khung thời gian: 1_day, 1_week, 1_month")):
    """
    API lấy dữ liệu dự đoán cho từng mã cổ phiếu.
    Hỗ trợ chọn khung thời gian phân tích.
    """
    data = get_stock_predictions(interval)
    
    # Tính tổng hợp
    total = len(data)
    buy_count = sum(1 for p in data if "MUA" in p["recommendation"])
    sell_count = sum(1 for p in data if "BÁN" in p["recommendation"])
    neutral_count = sum(1 for p in data if p["recommendation"] == "GIỮ")
    
    return {
        "status": "success",
        "interval": interval,
        "interval_label": INTERVAL_LABELS.get(interval, interval),
        "summary": {
            "total": total,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "neutral_count": neutral_count,
        },
        "data": data,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }


@app.get("/api/market-summary")
def market_summary():
    """
    API tổng hợp nhanh thị trường.
    """
    result = get_market_summary()
    return {"status": "success", **result}


# Mount static files - đặt SAU các API routes
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def read_index():
    """Phục vụ trang chủ."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Trang web chưa được khởi tạo đầy đủ."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
