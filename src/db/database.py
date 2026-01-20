"""数据库操作"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from .models import CheckIn


DB_PATH = Path(__file__).parent / "lol.db"


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS check_ins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            media_files TEXT DEFAULT '[]',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def create_checkin(content: str, media_files: List[str], ip_address: Optional[str] = None) -> int:
    """创建打卡记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    media_json = json.dumps(media_files)
    created_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO check_ins (content, media_files, created_at, ip_address)
        VALUES (?, ?, ?, ?)
    """, (content, media_json, created_at, ip_address))
    
    checkin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return checkin_id


def get_checkins(page: int = 1, limit: int = 20) -> Tuple[List[CheckIn], int]:
    """获取打卡记录列表
    
    Returns:
        (记录列表, 总数)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取总数
    cursor.execute("SELECT COUNT(*) as count FROM check_ins")
    total = cursor.fetchone()["count"]
    
    # 获取分页数据
    offset = (page - 1) * limit
    cursor.execute("""
        SELECT id, content, media_files, created_at, ip_address
        FROM check_ins
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    checkins = []
    for row in rows:
        checkin = CheckIn(
            id=row["id"],
            content=row["content"],
            media_files=row["media_files"],
            created_at=datetime.fromisoformat(row["created_at"]),
            ip_address=row["ip_address"]
        )
        checkins.append(checkin)
    
    return checkins, total


def get_checkin_by_id(checkin_id: int) -> Optional[CheckIn]:
    """根据ID获取打卡记录"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, content, media_files, created_at, ip_address
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
            ip_address=row["ip_address"]
        )
    return None


# 应用启动时初始化数据库
init_db()
