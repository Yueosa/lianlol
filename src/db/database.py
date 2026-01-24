"""数据库操作 - 兼容层
保持原有 API 不变，内部委托给新的模块化实现
"""
from typing import List, Optional, Tuple

from .models import CheckIn
from .schema import init_db
from .repositories import checkin as checkin_repo
from .repositories import like as like_repo

# 重新导出常量
from .connection import DB_PATH, DB_VERSION


def create_checkin(
    content: str,
    media_files: List[str],
    ip_address: Optional[str] = None,
    nickname: str = "用户0721",
    email: Optional[str] = None,
    qq: Optional[str] = None,
    url: Optional[str] = None,
    avatar: str = "🥰",
    file_type: str = "media",
    archive_metadata: Optional[str] = None,
    approved: bool = True
) -> int:
    """创建打卡记录"""
    return checkin_repo.create(
        content=content,
        media_files=media_files,
        ip_address=ip_address,
        nickname=nickname,
        email=email,
        qq=qq,
        url=url,
        avatar=avatar,
        file_type=file_type,
        archive_metadata=archive_metadata,
        approved=approved
    )


def get_checkins(
    page: int = 1,
    limit: int = 20,
    sort_order: str = "desc",
    sort_by: str = "id",
    nickname: Optional[str] = None,
    email: Optional[str] = None,
    content_keyword: Optional[str] = None,
    exclude_default_nickname: bool = False,
    min_content_length: Optional[int] = None
) -> Tuple[List[CheckIn], int]:
    """获取打卡记录列表"""
    return checkin_repo.get_list(
        page=page,
        limit=limit,
        sort_order=sort_order,
        sort_by=sort_by,
        nickname=nickname,
        email=email,
        content_keyword=content_keyword,
        exclude_default_nickname=exclude_default_nickname,
        min_content_length=min_content_length
    )


def get_checkin_by_id(checkin_id: int) -> Optional[CheckIn]:
    """根据ID获取打卡记录"""
    return checkin_repo.get_by_id(checkin_id)


def add_like(checkin_id: int, ip_address: str) -> Tuple[bool, int, str]:
    """给记录点赞"""
    return like_repo.add(checkin_id, ip_address)


def check_liked(checkin_id: int, ip_address: str) -> bool:
    """检查是否已点赞"""
    return like_repo.check(checkin_id, ip_address)


def get_liked_checkins(ip_address: str) -> List[int]:
    """获取某IP已点赞的所有记录ID"""
    return like_repo.get_liked_ids(ip_address)


# 应用启动时初始化数据库
init_db()
