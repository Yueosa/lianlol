"""撸了吗 - 打卡系统主程序"""
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# 加载环境变量
load_dotenv()

from src.api.routes import router as api_router
from src.api.admin import router as admin_router
from src.utils.security import is_blocked_country


# ============ 安全中间件 ============

class SecurityMiddleware(BaseHTTPMiddleware):
    """全局安全中间件：检查 IP 封锁"""
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端 IP
        client_ip = request.client.host if request.client else None
        
        if client_ip:
            # 检查是否来自被封锁的国家
            is_blocked, country = is_blocked_country(client_ip)
            
            if is_blocked:
                # 对于 API 请求返回 JSON
                if request.url.path.startswith("/api/"):
                    return JSONResponse(
                        status_code=451,
                        content={
                            "success": False,
                            "message": f"此服务在您所在的地区 ({country}) 不可用",
                            "error": "REGION_BLOCKED"
                        }
                    )
                # 对于页面请求返回 HTML
                else:
                    return HTMLResponse(
                        status_code=451,
                        content=f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <title>451 Unavailable For Legal Reasons</title>
                            <style>
                                body {{ 
                                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                                    display: flex; 
                                    justify-content: center; 
                                    align-items: center; 
                                    height: 100vh; 
                                    margin: 0;
                                    background: #1a1a2e;
                                    color: #eee;
                                }}
                                .container {{ text-align: center; padding: 2rem; }}
                                h1 {{ font-size: 4rem; margin: 0; color: #e94560; }}
                                p {{ font-size: 1.2rem; color: #aaa; }}
                                code {{ background: #16213e; padding: 0.2rem 0.5rem; border-radius: 4px; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <h1>451</h1>
                                <p>Unavailable For Legal Reasons</p>
                                <p>此服务在您所在的地区 (<code>{country}</code>) 不可用</p>
                                <p style="font-size: 0.9rem; margin-top: 2rem;">
                                    HTTP 451 是一个具有讽刺意味的状态码，<br>
                                    来源于雷·布雷德伯里的小说《华氏451度》
                                </p>
                            </div>
                        </body>
                        </html>
                        """
                    )
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加安全响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:;"
        
        return response


# 创建 FastAPI 应用
app = FastAPI(title="撸了吗", description="一个支持多媒体的打卡系统", version="0.1.0")

# 添加安全中间件
app.add_middleware(SecurityMiddleware)

# 挂载静态文件目录
static_dir = Path(__file__).parent / "src" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 配置 Jinja2 模板
templates_dir = Path(__file__).parent / "src" / "html"
templates = Jinja2Templates(directory=templates_dir)

# 挂载 API 路由
app.include_router(api_router)
app.include_router(admin_router)


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


@app.get("/admin")
async def admin_page(request: Request):
    """管理后台页面"""
    return templates.TemplateResponse(
        "admin.jinja2",
        {"request": request, "active_page": "admin"}
    )


def main():
    """启动应用"""
    admin_key = os.getenv("ADMIN_KEY", "")
    
    print("🚀 启动撸了吗打卡系统...")
    print("📍 访问地址: http://localhost:8722")
    print("📝 打卡提交: http://localhost:8722/")
    print("📊 打卡展示: http://localhost:8722/display")
    print("⚙️ 管理面板: http://localhost:8722/admin")
    if admin_key:
        print(f"🔑 管理密钥: {admin_key}")
    else:
        print("⚠️  未设置 ADMIN_KEY，请在 .env 文件中配置")
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
