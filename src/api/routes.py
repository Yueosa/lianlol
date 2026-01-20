"""API 路由"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse

import sys
sys.path.append(str(Path(__file__).parent.parent))

from db.database import create_checkin, get_checkins


router = APIRouter(prefix="/api")

# 文件上传配置
UPLOAD_DIR = Path(__file__).parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "video": [".mp4", ".webm", ".mov", ".avi"]
}


def get_file_type(filename: str) -> str:
    """获取文件类型"""
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_EXTENSIONS["image"]:
        return "image"
    elif ext in ALLOWED_EXTENSIONS["video"]:
        return "video"
    return "unknown"


def is_allowed_file(filename: str) -> bool:
    """检查文件是否允许上传"""
    ext = Path(filename).suffix.lower()
    all_allowed = ALLOWED_EXTENSIONS["image"] + ALLOWED_EXTENSIONS["video"]
    return ext in all_allowed


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传单个文件"""
    # 验证文件类型
    if not is_allowed_file(file.filename):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "不支持的文件格式"}
        )
    
    # 读取文件内容
    content = await file.read()
    file_size = len(content)
    
    # 验证文件大小
    if file_size > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "文件大小超过20MB限制"}
        )
    
    # 生成唯一文件名
    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # 按年月组织目录
    now = datetime.now()
    date_dir = UPLOAD_DIR / f"{now.year}-{now.month:02d}"
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    file_path = date_dir / unique_filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    # 返回相对路径
    relative_path = f"/static/uploads/{now.year}-{now.month:02d}/{unique_filename}"
    
    return {
        "success": True,
        "filename": unique_filename,
        "url": relative_path,
        "type": get_file_type(file.filename)
    }


@router.post("/checkin")
async def create_checkin_record(
    request: Request,
    content: str = Form(...),
    files: List[UploadFile] = File(default=[])
):
    """创建打卡记录"""
    # 获取客户端IP
    client_ip = request.client.host if request.client else None
    
    # 处理上传的文件
    media_files = []
    for file in files:
        if file.filename:
            # 上传文件
            upload_result = await upload_file(file)
            if isinstance(upload_result, dict) and upload_result.get("success"):
                media_files.append({
                    "url": upload_result["url"],
                    "type": upload_result["type"],
                    "filename": upload_result["filename"]
                })
    
    # 将媒体文件列表转为JSON字符串列表（仅保存URL）
    media_urls = [f["url"] for f in media_files]
    
    # 创建打卡记录
    checkin_id = create_checkin(content, media_urls, client_ip)
    
    return {
        "success": True,
        "message": "打卡成功",
        "id": checkin_id,
        "media_count": len(media_files)
    }


@router.get("/checkins")
async def get_checkin_list(page: int = 1, limit: int = 20):
    """获取打卡记录列表"""
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20
    
    checkins, total = get_checkins(page, limit)
    
    # 转换为字典列表
    checkin_list = []
    for checkin in checkins:
        checkin_dict = checkin.to_dict()
        # 解析 media_files JSON 字符串
        checkin_dict["media_files"] = json.loads(checkin_dict["media_files"])
        checkin_list.append(checkin_dict)
    
    return {
        "success": True,
        "data": checkin_list,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }
