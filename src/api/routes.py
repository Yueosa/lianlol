"""API 路由"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse

import sys
sys.path.append(str(Path(__file__).parent.parent))

from db.database import create_checkin, get_checkins, add_like, get_liked_checkins, get_checkin_by_id
from utils.validators import (
    validate_email,
    validate_url,
    validate_qq,
    validate_nickname,
    validate_emoji,
    validate_content,
    validate_all_fields,
    sanitize_html,
    auto_review_content
)
from utils.security import (
    security_check,
    is_blocked_country,
    add_to_blacklist
)
from utils.archive_handler import (
    is_archive_file,
    validate_archive,
    extract_preview_images,
    ArchiveHandler
)


router = APIRouter(prefix="/api")

# 文件上传配置
UPLOAD_DIR = Path(__file__).parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "video": [".mp4", ".webm", ".mov", ".avi"],
    "archive": [".zip", ".7z"]
}


def get_file_type(filename: str) -> str:
    """获取文件类型"""
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_EXTENSIONS["image"]:
        return "image"
    elif ext in ALLOWED_EXTENSIONS["video"]:
        return "video"
    elif ext in ALLOWED_EXTENSIONS["archive"]:
        return "archive"
    return "unknown"


def is_allowed_file(filename: str) -> bool:
    """检查文件是否允许上传"""
    ext = Path(filename).suffix.lower()
    all_allowed = ALLOWED_EXTENSIONS["image"] + ALLOWED_EXTENSIONS["video"] + ALLOWED_EXTENSIONS["archive"]
    return ext in all_allowed


@router.post("/archive/fullimage")
async def get_archive_full_image(file: UploadFile = File(...), path: str = Form(...)):
    """获取压缩包中某张图片的大图预览"""
    # 验证文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS["archive"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "只支持 ZIP 和 7Z 格式"}
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 保存到临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        handler = ArchiveHandler(tmp_path)
        full_image = handler.get_full_image(path)
        
        if full_image:
            return {"success": True, "image": full_image}
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无法获取图片"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"获取图片失败: {str(e)}"}
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/archive/preview")
async def preview_archive(file: UploadFile = File(...)):
    """预览压缩包内容（不保存文件，仅返回图片列表和缩略图）"""
    # 验证文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS["archive"]:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "只支持 ZIP 和 7Z 格式"}
        )
    
    # 读取文件内容
    content = await file.read()
    file_size = len(content)
    
    # 验证文件大小
    if file_size > MAX_FILE_SIZE:
        size_mb = MAX_FILE_SIZE / 1024 / 1024
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"文件大小超过{size_mb:.0f}MB限制"}
        )
    
    # 保存到临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # 验证压缩包（包含恶意文件检测）
        is_valid, error_msg = validate_archive(tmp_path)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": error_msg}
            )
        
        # 获取图片列表
        handler = ArchiveHandler(tmp_path)
        image_list = handler.list_images()
        metadata = handler.get_metadata()
        
        # 生成缩略图（最多50张）
        images_with_thumbnails = handler.get_thumbnails(image_list, max_count=50)
        
        return {
            "success": True,
            "filename": file.filename,
            "size": file_size,
            "archive_info": {
                "image_count": len(image_list),
                "images": images_with_thumbnails,  # 包含缩略图
                "total_files": metadata.get("total_files", 0)
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"解析压缩包失败: {str(e)}"}
        )
    finally:
        # 清理临时文件
        tmp_path.unlink(missing_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传单个文件（支持图片、视频、压缩包）"""
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
        size_mb = MAX_FILE_SIZE / 1024 / 1024
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"文件大小超过{size_mb:.0f}MB限制"}
        )
    
    # 生成唯一文件名
    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # 按年月组织目录
    now = datetime.now()
    date_dir = UPLOAD_DIR / f"{now.year}-{now.month:02d}"
    
    file_type = get_file_type(file.filename)
    
    # 如果是压缩包，保存到 archives 子目录
    if file_type == "archive":
        date_dir = date_dir / "archives"
    
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存文件
    file_path = date_dir / unique_filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    # 返回相对路径
    if file_type == "archive":
        relative_path = f"/static/uploads/{now.year}-{now.month:02d}/archives/{unique_filename}"
    else:
        relative_path = f"/static/uploads/{now.year}-{now.month:02d}/{unique_filename}"
    
    result = {
        "success": True,
        "filename": unique_filename,
        "url": relative_path,
        "type": file_type
    }
    
    # 如果是压缩包，列出其中的图片文件
    if file_type == "archive":
        # 验证压缩包
        is_valid, error_msg = validate_archive(file_path)
        if not is_valid:
            # 删除无效文件
            file_path.unlink(missing_ok=True)
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": error_msg}
            )
        
        try:
            handler = ArchiveHandler(file_path)
            image_list = handler.list_images()
            result["archive_info"] = {
                "image_count": len(image_list),
                "images": image_list[:50]  # 最多返回50个图片文件名
            }
        except Exception as e:
            result["archive_info"] = {"error": str(e)}
    
    return result


@router.post("/checkin")
async def create_checkin_record(
    request: Request,
    content: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    nickname: str = Form(default="用户0721"),
    email: Optional[str] = Form(default=None),
    qq: Optional[str] = Form(default=None),
    url: Optional[str] = Form(default=None),
    avatar: str = Form(default="🥰"),
    # 压缩包预览图选择（JSON字符串）
    archive_preview_images: Optional[str] = Form(default=None),
    # 蜜罐字段（正常用户看不到，不会填写）
    website: Optional[str] = Form(default=None),  # honeypot
    form_token: Optional[str] = Form(default=None)  # 表单时间戳
):
    """创建打卡记录"""
    # 获取客户端IP
    client_ip = request.client.host if request.client else None
    
    # === 安全检查 ===
    is_allowed, status_code, error_msg = security_check(
        ip=client_ip or "unknown",
        action="write",
        content=content,
        honeypot_value=website,  # 蜜罐字段
        form_timestamp=form_token
    )
    
    if not is_allowed:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": error_msg}
        )
    
    # === 综合字段安全验证 ===
    is_valid, error_msg = validate_all_fields(
        content=content,
        nickname=nickname,
        email=email,
        qq=qq,
        url=url
    )
    if not is_valid:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": error_msg}
        )
    
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
    
    # 处理上传的文件
    media_files = []
    archive_file_path = None
    archive_metadata_dict = None
    file_type_flag = "media"  # 默认为普通媒体文件
    original_archive_name = None  # 压缩包原始文件名
    archive_file_count = 0  # 压缩包文件数量（不含预览图）
    
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
                
                # 如果是压缩包，记录路径和原始文件名
                if upload_result["type"] == "archive":
                    file_type_flag = "archive"
                    original_archive_name = file.filename  # 保存原始文件名
                    archive_file_count = 1
                    # 从 URL 构建文件路径
                    archive_url = upload_result["url"]
                    archive_file_path = Path(__file__).parent.parent / archive_url.lstrip("/")
    
    # 如果是压缩包，处理预览图
    if file_type_flag == "archive" and archive_file_path and archive_file_path.exists():
        now = datetime.now()
        # 为这个打卡记录创建预览图目录
        preview_dir = UPLOAD_DIR / f"{now.year}-{now.month:02d}" / "previews" / archive_file_path.stem
        
        # 解析用户选择的预览图（如果有）
        selected_images = None
        if archive_preview_images:
            try:
                selected_images = json.loads(archive_preview_images)
            except:
                pass
        
        try:
            # 提取预览图
            preview_urls, metadata = extract_preview_images(
                archive_file_path,
                preview_dir,
                selected_images=selected_images,
                auto_select_count=3
            )
            
            # 将预览图URL添加到media_files
            media_files.extend([
                {"url": url, "type": "preview", "filename": Path(url).name}
                for url in preview_urls
            ])
            
            # 保存元数据，使用原始文件名
            metadata["filename"] = original_archive_name or metadata.get("filename", "archive")
            archive_metadata_dict = metadata
            
        except Exception as e:
            print(f"提取压缩包预览图失败: {str(e)}")
    
    # 将媒体文件列表转为JSON字符串列表（仅保存URL）
    media_urls = [f["url"] for f in media_files]
    
    # 处理空值（并进行 HTML 转义防止 XSS）
    nickname = sanitize_html(nickname.strip()) if nickname and nickname.strip() else "用户0721"
    email = email.strip() if email and email.strip() else None
    qq = qq.strip() if qq and qq.strip() else None
    url = url.strip() if url and url.strip() else None
    avatar = avatar.strip() if avatar and avatar.strip() else "🥰"
    content = sanitize_html(content.strip())  # 内容也转义
    
    # === 自动审核检测 ===
    has_media = len(media_files) > 0
    auto_approved, review_reason = auto_review_content(
        content=content,
        has_media=has_media,
        nickname=nickname
    )
    
    # 创建打卡记录
    checkin_id = create_checkin(
        content=content,
        media_files=media_urls,
        ip_address=client_ip,
        nickname=nickname,
        email=email,
        qq=qq,
        url=url,
        avatar=avatar,
        file_type=file_type_flag,
        archive_metadata=json.dumps(archive_metadata_dict) if archive_metadata_dict else None,
        approved=auto_approved
    )
    
    # 根据审核结果返回不同的消息
    if auto_approved:
        return {
            "success": True,
            "message": "打卡成功",
            "id": checkin_id,
            "media_count": archive_file_count if file_type_flag == "archive" else len(media_files)
        }
    else:
        return {
            "success": True,
            "message": "提交成功，内容需要审核后才会显示",
            "id": checkin_id,
            "media_count": archive_file_count if file_type_flag == "archive" else len(media_files),
            "pending_review": True
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
    # 获取客户端 IP
    client_ip = request.client.host if request.client else None
    
    # 安全检查（读取操作）
    is_allowed, status_code, error_msg = security_check(
        ip=client_ip or "unknown",
        action="read"
    )
    
    if not is_allowed:
        return JSONResponse(
            status_code=status_code,
            content={"success": False, "message": error_msg}
        )
    
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


@router.get("/download/{checkin_id}")
async def download_archive(checkin_id: int):
    """下载打卡记录的压缩包
    
    Args:
        checkin_id: 记录ID
    """
    # 获取打卡记录
    checkin = get_checkin_by_id(checkin_id)
    
    if not checkin:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 检查是否为压缩包类型
    if checkin.file_type != "archive":
        raise HTTPException(status_code=400, detail="该记录不包含压缩包")
    
    # 解析 media_files 找到压缩包文件
    try:
        media_files = json.loads(checkin.media_files)
    except:
        raise HTTPException(status_code=500, detail="数据格式错误")
    
    # 找到压缩包文件
    archive_url = None
    for url in media_files:
        if '/archives/' in url and (url.endswith('.zip') or url.endswith('.7z')):
            archive_url = url
            break
    
    if not archive_url:
        raise HTTPException(status_code=404, detail="未找到压缩包文件")
    
    # 构建文件路径
    file_path = Path(__file__).parent.parent / archive_url.lstrip("/")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 获取原始文件名（从元数据中）
    original_filename = file_path.name
    if checkin.archive_metadata:
        try:
            metadata = json.loads(checkin.archive_metadata)
            original_filename = metadata.get("filename", file_path.name)
        except:
            pass
    
    # 返回文件下载
    return FileResponse(
        path=file_path,
        filename=original_filename,
        media_type='application/octet-stream'
    )

