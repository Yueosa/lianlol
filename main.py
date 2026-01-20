"""撸了吗 - 打卡系统主程序"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from src.api.routes import router as api_router


# 创建 FastAPI 应用
app = FastAPI(title="撸了吗", description="一个支持多媒体的打卡系统", version="0.1.0")

# 挂载静态文件目录
static_dir = Path(__file__).parent / "src" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 挂载 API 路由
app.include_router(api_router)


@app.get("/")
async def index():
    """首页 - 打卡提交页面"""
    html_path = Path(__file__).parent / "src" / "html" / "index.html"
    return FileResponse(html_path)


@app.get("/display")
async def display():
    """打卡展示页面"""
    html_path = Path(__file__).parent / "src" / "html" / "display.html"
    return FileResponse(html_path)


def main():
    """启动应用"""
    print("🚀 启动撸了吗打卡系统...")
    print("📍 访问地址: http://localhost:8000")
    print("📝 打卡提交: http://localhost:8000/")
    print("📊 打卡展示: http://localhost:8000/display")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
