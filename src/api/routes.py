"""API 路由"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Query
from fastapi.responses import JSONResponse

import sys
sys.path.append(str(Path(__file__).parent.parent))

from db.database import create_checkin, get_checkins, add_like, get_liked_checkins
from utils.validators import (
    validate_email,
    validate_url,
    validate_qq,
    validate_nickname,
    validate_emoji,
    validate_content
)


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
    files: List[UploadFile] = File(default=[]),
    nickname: str = Form(default="用户0721"),
    email: Optional[str] = Form(default=None),
    qq: Optional[str] = Form(default=None),
    url: Optional[str] = Form(default=None),
    avatar: str = Form(default="🥰")
):
    """创建打卡记录"""
    # 验证内容
    is_valid, error_msg = validate_content(content)
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": error_msg}
        )
    
    # 验证昵称
    is_valid, error_msg = validate_nickname(nickname)
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": error_msg}
        )
    
    # 验证邮箱
    is_valid, error_msg = validate_email(email)
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": error_msg}
        )
    
    # 验证 QQ 号
    is_valid, error_msg = validate_qq(qq)
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": error_msg}
        )
    
    # 验证 URL
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": error_msg}
        )
    
    # 验证头像 emoji
    is_valid, error_msg = validate_emoji(avatar)
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": error_msg}
        )
    
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
    
    # 处理空值
    nickname = nickname.strip() if nickname and nickname.strip() else "用户0721"
    email = email.strip() if email and email.strip() else None
    qq = qq.strip() if qq and qq.strip() else None
    url = url.strip() if url and url.strip() else None
    avatar = avatar.strip() if avatar and avatar.strip() else "🥰"
    
    # 创建打卡记录
    checkin_id = create_checkin(
        content=content,
        media_files=media_urls,
        ip_address=client_ip,
        nickname=nickname,
        email=email,
        qq=qq,
        url=url,
        avatar=avatar
    )
    
    return {
        "success": True,
        "message": "打卡成功",
        "id": checkin_id,
        "media_count": len(media_files)
    }


@router.get("/checkins")
async def get_checkin_list(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
    sort_by: str = Query(default="id", pattern="^(id|love)$"),
    nickname: Optional[str] = Query(default=None),
    email: Optional[str] = Query(default=None),
    content: Optional[str] = Query(default=None),
    exclude_default_nickname: bool = Query(default=False),
    min_content_length: Optional[int] = Query(default=None, ge=0)
):
    """获取打卡记录列表（支持搜索和筛选）
    
    Args:
        page: 页码
        limit: 每页数量
        sort: 排序方式 (asc=正序, desc=倒序)
        sort_by: 排序字段 (id=按ID, love=按点赞数)
        nickname: 昵称（模糊搜索）
        email: 邮箱（精确搜索）
        content: 内容关键词（模糊搜索）
        exclude_default_nickname: 排除默认昵称用户
        min_content_length: 最小内容长度
    """
    checkins, total = get_checkins(
        page=page,
        limit=limit,
        sort_order=sort,
        sort_by=sort_by,
        nickname=nickname,
        email=email,
        content_keyword=content,
        exclude_default_nickname=exclude_default_nickname,
        min_content_length=min_content_length
    )
    
    # 获取当前用户已点赞的记录
    client_ip = request.client.host if request.client else None
    liked_ids = get_liked_checkins(client_ip) if client_ip else []
    
    # 转换为字典列表
    checkin_list = []
    for checkin in checkins:
        checkin_dict = checkin.to_dict()
        # 解析 media_files JSON 字符串
        checkin_dict["media_files"] = json.loads(checkin_dict["media_files"])
        # 添加是否已点赞标记
        checkin_dict["liked"] = checkin.id in liked_ids
        checkin_list.append(checkin_dict)
    
    return {
        "success": True,
        "data": checkin_list,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.post("/like/{checkin_id}")
async def like_checkin(checkin_id: int, request: Request):
    """给记录点赞
    
    Args:
        checkin_id: 记录ID
    """
    client_ip = request.client.host if request.client else None
    
    if not client_ip:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "无法获取您的IP地址"}
        )
    
    success, love_count, message = add_like(checkin_id, client_ip)
    
    return {
        "success": success,
        "message": message,
        "love": love_count,
        "liked": True if success else None  # 成功时标记为已点赞
    }
