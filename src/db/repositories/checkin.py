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
    avatar: str = "🥰"
) -> int:
    """创建打卡记录
    
    Returns:
        新记录的ID
    """
    media_json = json.dumps(media_files)
    created_at = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO check_ins (
                content, media_files, created_at, ip_address,
                nickname, email, qq, url, avatar
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (content, media_json, created_at, ip_address, nickname, email, qq, url, avatar))
        
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
    min_content_length: Optional[int] = None
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
    
    Returns:
        (记录列表, 总数)
    """
    # 构建 WHERE 条件
    where_clauses = []
    params = []
    
    if nickname:
        where_clauses.append("nickname LIKE ?")
        params.append(f"%{nickname}%")
    
    if email:
        where_clauses.append("email = ?")
        params.append(email)
    
    if content_keyword:
        where_clauses.append("content LIKE ?")
        params.append(f"%{content_keyword}%")
    
    if exclude_default_nickname:
        where_clauses.append("nickname != '用户0721'")
    
    if min_content_length is not None and min_content_length > 0:
        where_clauses.append("LENGTH(content) >= ?")
        params.append(min_content_length)
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # 排序字段和方向
    sort_column = "love" if sort_by == "love" else "id"
    order_direction = "ASC" if sort_order == "asc" else "DESC"
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取总数
        count_sql = f"SELECT COUNT(*) as count FROM check_ins WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["count"]
        
        # 获取分页数据
        offset = (page - 1) * limit
        data_sql = f"""
            SELECT id, content, media_files, created_at, ip_address,
                   nickname, email, qq, url, avatar, love
            FROM check_ins
            WHERE {where_sql}
            ORDER BY {sort_column} {order_direction}
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
                   nickname, email, qq, url, avatar, love
            FROM check_ins
            WHERE id = ?
        """, (checkin_id,))
        
        row = cursor.fetchone()
    
    return _row_to_checkin(row) if row else None


def _row_to_checkin(row) -> CheckIn:
    """将数据库行转换为 CheckIn 对象"""
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
        love=row["love"] or 0
    )
