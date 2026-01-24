"""打卡记录数据访问层"""
import json
from datetime import datetime
from typing import List, Optional, Tuple

from ..models import CheckIn
from ..connection import get_db


def create(
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
    """创建打卡记录
    
    Returns:
        新记录的ID
    """
    media_json = json.dumps(media_files)
    created_at = datetime.now().isoformat()
    approved_int = 1 if approved else 0
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO check_ins (
                content, media_files, created_at, ip_address,
                nickname, email, qq, url, avatar, file_type, archive_metadata, approved
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (content, media_json, created_at, ip_address, nickname, email, qq, url, avatar, file_type, archive_metadata, approved_int))
        
        return cursor.lastrowid


def get_list(
    page: int = 1,
    limit: int = 20,
    sort_order: str = "desc",
    sort_by: str = "id",
    nickname: Optional[str] = None,
    email: Optional[str] = None,
    content_keyword: Optional[str] = None,
    exclude_default_nickname: bool = False,
    min_content_length: Optional[int] = None,
    approved_only: bool = True
) -> Tuple[List[CheckIn], int]:
    """获取打卡记录列表（支持搜索和筛选）
    
    Args:
        page: 页码
        limit: 每页数量
        sort_order: 排序方式 (asc=正序, desc=倒序)
        sort_by: 排序字段 (id=按ID, love=按点赞数)
        nickname: 昵称（模糊搜索）
        email: 邮箱（精确搜索）
        content_keyword: 内容关键词（模糊搜索）
        exclude_default_nickname: 排除默认昵称用户
        min_content_length: 最小内容长度
        approved_only: 仅显示已审核通过的记录（默认 True）
    
    Returns:
        (记录列表, 总数)
    """
    # 构建 WHERE 条件（使用 numbered 表别名前缀）
    where_clauses = []
    params = []
    
    if nickname:
        where_clauses.append("numbered.nickname LIKE ?")
        params.append(f"%{nickname}%")
    
    if email:
        where_clauses.append("numbered.email = ?")
        params.append(email)
    
    if content_keyword:
        where_clauses.append("numbered.content LIKE ?")
        params.append(f"%{content_keyword}%")
    
    if exclude_default_nickname:
        where_clauses.append("numbered.nickname != '用户0721'")
    
    if min_content_length is not None and min_content_length > 0:
        where_clauses.append("LENGTH(numbered.content) >= ?")
        params.append(min_content_length)
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # 排序字段和方向
    sort_column = "love" if sort_by == "love" else "id"
    order_direction = "ASC" if sort_order == "asc" else "DESC"
    
    # 审核过滤条件（用于子查询）
    approved_filter = "WHERE approved = 1" if approved_only else ""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取总数（这里用原始表名）
        count_where = where_sql.replace("numbered.", "")
        if approved_only:
            count_where = f"approved = 1 AND ({count_where})"
        count_sql = f"SELECT COUNT(*) as count FROM check_ins WHERE {count_where}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["count"]
        
        # 获取分页数据，使用 ROW_NUMBER() 计算连续编号
        # 注意：display_number 只计算已审核通过的记录
        offset = (page - 1) * limit
        data_sql = f"""
            SELECT 
                numbered.*
            FROM (
                SELECT 
                    id, content, media_files, created_at, ip_address,
                    nickname, email, qq, url, avatar, love, file_type, archive_metadata,
                    approved, reviewed_at,
                    ROW_NUMBER() OVER (ORDER BY created_at ASC) as display_number
                FROM check_ins
                {approved_filter}
            ) AS numbered
            WHERE {where_sql}
            ORDER BY numbered.{sort_column} {order_direction}
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_sql, params + [limit, offset])
        rows = cursor.fetchall()
    
    checkins = [_row_to_checkin(row) for row in rows]
    return checkins, total


def get_by_id(checkin_id: int) -> Optional[CheckIn]:
    """根据ID获取打卡记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, content, media_files, created_at, ip_address,
                   nickname, email, qq, url, avatar, love, file_type, archive_metadata,
                   approved, reviewed_at
            FROM check_ins
            WHERE id = ?
        """, (checkin_id,))
        
        row = cursor.fetchone()
    
    return _row_to_checkin(row) if row else None


def get_pending_list(page: int = 1, limit: int = 20) -> Tuple[List[CheckIn], int]:
    """获取待审核记录列表
    
    Returns:
        (记录列表, 总数)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取总数
        cursor.execute("SELECT COUNT(*) as count FROM check_ins WHERE approved = 0")
        total = cursor.fetchone()["count"]
        
        # 获取分页数据
        offset = (page - 1) * limit
        cursor.execute("""
            SELECT id, content, media_files, created_at, ip_address,
                   nickname, email, qq, url, avatar, love, file_type, archive_metadata,
                   approved, reviewed_at
            FROM check_ins
            WHERE approved = 0
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()
    
    checkins = [_row_to_checkin(row) for row in rows]
    return checkins, total


def approve(checkin_id: int) -> bool:
    """通过审核
    
    Returns:
        是否成功
    """
    reviewed_at = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE check_ins 
            SET approved = 1, reviewed_at = ?
            WHERE id = ?
        """, (reviewed_at, checkin_id))
        return cursor.rowcount > 0


def reject(checkin_id: int) -> bool:
    """拒绝审核（删除记录）
    
    Returns:
        是否成功
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM check_ins WHERE id = ?", (checkin_id,))
        return cursor.rowcount > 0


def ban(checkin_id: int) -> bool:
    """封禁已发布内容（将 approved 设为 0）
    
    Returns:
        是否成功
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE check_ins 
            SET approved = 0
            WHERE id = ?
        """, (checkin_id,))
        return cursor.rowcount > 0


def get_stats() -> dict:
    """获取统计信息"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM check_ins")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM check_ins WHERE approved = 1")
        approved = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM check_ins WHERE approved = 0")
        pending = cursor.fetchone()[0]
        
    return {
        "total": total,
        "approved": approved,
        "pending": pending
    }


def _row_to_checkin(row) -> CheckIn:
    """将数据库行转换为 CheckIn 对象"""
    # 获取新字段，兼容旧数据
    try:
        file_type = row["file_type"] or "media"
    except (KeyError, IndexError):
        file_type = "media"
    
    try:
        archive_metadata = row["archive_metadata"]
    except (KeyError, IndexError):
        archive_metadata = None
    
    try:
        display_number = row["display_number"]
    except (KeyError, IndexError):
        display_number = None
    
    try:
        approved = bool(row["approved"]) if row["approved"] is not None else True
    except (KeyError, IndexError):
        approved = True
    
    try:
        reviewed_at_str = row["reviewed_at"]
        reviewed_at = datetime.fromisoformat(reviewed_at_str) if reviewed_at_str else None
    except (KeyError, IndexError):
        reviewed_at = None
    
    return CheckIn(
        id=row["id"],
        content=row["content"],
        media_files=row["media_files"],
        created_at=datetime.fromisoformat(row["created_at"]),
        ip_address=row["ip_address"],
        nickname=row["nickname"] or "用户0721",
        email=row["email"],
        qq=row["qq"],
        url=row["url"],
        avatar=row["avatar"] or "🥰",
        love=row["love"] or 0,
        file_type=file_type,
        archive_metadata=archive_metadata,
        approved=approved,
        reviewed_at=reviewed_at,
        display_number=display_number
    )
