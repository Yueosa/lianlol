"""数据库操作"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from .models import CheckIn


DB_PATH = Path(__file__).parent / "lol.db"
DB_VERSION = "3.0"  # 当前数据库版本


def _check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def _check_table_exists(cursor, table_name: str) -> bool:
    """检查表是否存在"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def migrate_db():
    """数据库迁移 - 支持从任意旧版本升级到最新版本"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # V1.0 -> V2.0: 添加用户信息字段
    if not _check_column_exists(cursor, "check_ins", "nickname"):
        print("开始数据库迁移：V1.0 -> V2.0")
        cursor.execute("ALTER TABLE check_ins ADD COLUMN nickname TEXT DEFAULT '用户0721'")
        cursor.execute("ALTER TABLE check_ins ADD COLUMN email TEXT")
        cursor.execute("ALTER TABLE check_ins ADD COLUMN qq TEXT")
        cursor.execute("ALTER TABLE check_ins ADD COLUMN url TEXT")
        cursor.execute("ALTER TABLE check_ins ADD COLUMN avatar TEXT DEFAULT '🥰'")
        cursor.execute("UPDATE check_ins SET nickname = '用户0721' WHERE nickname IS NULL")
        cursor.execute("UPDATE check_ins SET avatar = '🥰' WHERE avatar IS NULL")
        conn.commit()
        print("数据库迁移完成：V1.0 -> V2.0")
    
    # V2.0 -> V3.0: 添加点赞功能
    if not _check_column_exists(cursor, "check_ins", "love"):
        print("开始数据库迁移：V2.0 -> V3.0")
        
        # 添加 love 字段
        cursor.execute("ALTER TABLE check_ins ADD COLUMN love INTEGER DEFAULT 0")
        cursor.execute("UPDATE check_ins SET love = 0 WHERE love IS NULL")
        
        # 创建 likes 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkin_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(checkin_id, ip_address),
                FOREIGN KEY (checkin_id) REFERENCES check_ins(id) ON DELETE CASCADE
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_likes_checkin_ip 
            ON likes(checkin_id, ip_address)
        """)
        
        conn.commit()
        print("数据库迁移完成：V2.0 -> V3.0")
    
    # 确保 likes 表存在（即使 love 字段存在，likes 表可能不存在）
    if not _check_table_exists(cursor, "likes"):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkin_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(checkin_id, ip_address),
                FOREIGN KEY (checkin_id) REFERENCES check_ins(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_likes_checkin_ip 
            ON likes(checkin_id, ip_address)
        """)
        conn.commit()
    
    conn.close()


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建表（V3.0 完整架构）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS check_ins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            media_files TEXT DEFAULT '[]',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            nickname TEXT DEFAULT '用户0721',
            email TEXT,
            qq TEXT,
            url TEXT,
            avatar TEXT DEFAULT '🥰',
            love INTEGER DEFAULT 0
        )
    """)
    
    # 创建点赞记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checkin_id INTEGER NOT NULL,
            ip_address TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(checkin_id, ip_address),
            FOREIGN KEY (checkin_id) REFERENCES check_ins(id) ON DELETE CASCADE
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_likes_checkin_ip 
        ON likes(checkin_id, ip_address)
    """)
    
    conn.commit()
    conn.close()
    
    # 执行迁移（如果需要）
    migrate_db()


def create_checkin(
    content: str,
    media_files: List[str],
    ip_address: Optional[str] = None,
    nickname: str = "用户0721",
    email: Optional[str] = None,
    qq: Optional[str] = None,
    url: Optional[str] = None,
    avatar: str = "🥰"
) -> int:
    """创建打卡记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    media_json = json.dumps(media_files)
    created_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO check_ins (
            content, media_files, created_at, ip_address,
            nickname, email, qq, url, avatar
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (content, media_json, created_at, ip_address, nickname, email, qq, url, avatar))
    
    checkin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return checkin_id


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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
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
    conn.close()
    
    checkins = []
    for row in rows:
        checkin = CheckIn(
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
        checkins.append(checkin)
    
    return checkins, total


def get_checkin_by_id(checkin_id: int) -> Optional[CheckIn]:
    """根据ID获取打卡记录"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, content, media_files, created_at, ip_address,
               nickname, email, qq, url, avatar, love
        FROM check_ins
        WHERE id = ?
    """, (checkin_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
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
    return None


def add_like(checkin_id: int, ip_address: str) -> Tuple[bool, int, str]:
    """给记录点赞
    
    Args:
        checkin_id: 记录ID
        ip_address: 点赞者IP
    
    Returns:
        (是否成功, 当前点赞数, 消息)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查记录是否存在
        cursor.execute("SELECT love FROM check_ins WHERE id = ?", (checkin_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, 0, "记录不存在"
        
        # 尝试插入点赞记录（如果已存在会失败）
        cursor.execute("""
            INSERT INTO likes (checkin_id, ip_address)
            VALUES (?, ?)
        """, (checkin_id, ip_address))
        
        # 更新点赞数
        cursor.execute("""
            UPDATE check_ins SET love = love + 1 WHERE id = ?
        """, (checkin_id,))
        
        conn.commit()
        
        # 获取最新点赞数
        cursor.execute("SELECT love FROM check_ins WHERE id = ?", (checkin_id,))
        new_love = cursor.fetchone()[0]
        
        conn.close()
        return True, new_love, "点赞成功"
        
    except sqlite3.IntegrityError:
        # 重复点赞
        cursor.execute("SELECT love FROM check_ins WHERE id = ?", (checkin_id,))
        current_love = cursor.fetchone()[0]
        conn.close()
        return False, current_love, "你已经点过赞了"
    except Exception as e:
        conn.close()
        return False, 0, f"点赞失败: {str(e)}"


def check_liked(checkin_id: int, ip_address: str) -> bool:
    """检查是否已点赞
    
    Args:
        checkin_id: 记录ID
        ip_address: IP地址
    
    Returns:
        是否已点赞
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 1 FROM likes 
        WHERE checkin_id = ? AND ip_address = ?
    """, (checkin_id, ip_address))
    
    result = cursor.fetchone() is not None
    conn.close()
    return result


def get_liked_checkins(ip_address: str) -> List[int]:
    """获取某IP已点赞的所有记录ID
    
    Args:
        ip_address: IP地址
    
    Returns:
        已点赞的记录ID列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT checkin_id FROM likes 
        WHERE ip_address = ?
    """, (ip_address,))
    
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result


# 应用启动时初始化数据库
init_db()
