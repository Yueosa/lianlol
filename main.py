"""撸了吗 - 打卡系统主程序"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from src.api.routes import router as api_router


# 创建 FastAPI 应用
app = FastAPI(title="撸了吗", description="一个支持多媒体的打卡系统", version="0.1.0")

# 挂载静态文件目录
static_dir = Path(__file__).parent / "src" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 配置 Jinja2 模板
templates_dir = Path(__file__).parent / "src" / "html"
templates = Jinja2Templates(directory=templates_dir)

# 挂载 API 路由
app.include_router(api_router)


@app.get("/")
async def index(request: Request):
    """首页 - 打卡提交页面"""
    return templates.TemplateResponse(
        "index.jinja2",
        {"request": request, "active_page": "index"}
    )


@app.get("/display")
async def display(request: Request):
    """打卡展示页面"""
    return templates.TemplateResponse(
        "display.jinja2",
        {"request": request, "active_page": "display"}
    )


def main():
    """启动应用"""
    print("🚀 启动撸了吗打卡系统...")
    print("📍 访问地址: http://localhost:8722")
    print("📝 打卡提交: http://localhost:8722/")
    print("📊 打卡展示: http://localhost:8722/display")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8722,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
