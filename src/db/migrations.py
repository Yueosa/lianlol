"""数据库迁移管理"""
import sqlite3
from .connection import DB_PATH


def _check_column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def _check_table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """检查表是否存在"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def migrate_v1_to_v2(cursor: sqlite3.Cursor, conn: sqlite3.Connection):
    """V1.0 -> V2.0: 添加用户信息字段"""
    if _check_column_exists(cursor, "check_ins", "nickname"):
        return
    
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


def migrate_v2_to_v3(cursor: sqlite3.Cursor, conn: sqlite3.Connection):
    """V2.0 -> V3.0: 添加点赞功能"""
    if _check_column_exists(cursor, "check_ins", "love"):
        return
    
    print("开始数据库迁移：V2.0 -> V3.0")
    
    # 添加 love 字段
    cursor.execute("ALTER TABLE check_ins ADD COLUMN love INTEGER DEFAULT 0")
    cursor.execute("UPDATE check_ins SET love = 0 WHERE love IS NULL")
    
    # 创建 likes 表
    _create_likes_table(cursor)
    
    conn.commit()
    print("数据库迁移完成：V2.0 -> V3.0")


def _create_likes_table(cursor: sqlite3.Cursor):
    """创建 likes 表"""
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


def ensure_likes_table(cursor: sqlite3.Cursor, conn: sqlite3.Connection):
    """确保 likes 表存在"""
    if _check_table_exists(cursor, "likes"):
        return
    
    _create_likes_table(cursor)
    conn.commit()


def migrate_v3_to_v4(cursor: sqlite3.Cursor, conn: sqlite3.Connection):
    """V3.0 -> V4.0: 添加压缩包支持"""
    if _check_column_exists(cursor, "check_ins", "file_type"):
        return
    
    print("开始数据库迁移：V3.0 -> V4.0")
    
    # 添加 file_type 字段
    cursor.execute("ALTER TABLE check_ins ADD COLUMN file_type TEXT DEFAULT 'media'")
    cursor.execute("UPDATE check_ins SET file_type = 'media' WHERE file_type IS NULL")
    
    # 添加 archive_metadata 字段
    cursor.execute("ALTER TABLE check_ins ADD COLUMN archive_metadata TEXT DEFAULT NULL")
    
    conn.commit()
    print("数据库迁移完成：V3.0 -> V4.0")


def migrate_v4_to_v5(cursor: sqlite3.Cursor, conn: sqlite3.Connection):
    """V4.0 -> V5.0: 添加内容审核功能"""
    if _check_column_exists(cursor, "check_ins", "approved"):
        # 检查是否需要添加 review_reason 字段
        if not _check_column_exists(cursor, "check_ins", "review_reason"):
            print("补充迁移：添加 review_reason 字段")
            cursor.execute("ALTER TABLE check_ins ADD COLUMN review_reason TEXT DEFAULT NULL")
            conn.commit()
        return
    
    print("开始数据库迁移：V4.0 -> V5.0")
    
    # 添加 approved 字段（默认为 1 表示已通过，新记录根据检测结果设置）
    cursor.execute("ALTER TABLE check_ins ADD COLUMN approved INTEGER DEFAULT 1")
    # 现有数据全部设为已通过
    cursor.execute("UPDATE check_ins SET approved = 1 WHERE approved IS NULL")
    
    # 添加 reviewed_at 字段
    cursor.execute("ALTER TABLE check_ins ADD COLUMN reviewed_at DATETIME DEFAULT NULL")
    
    # 添加 review_reason 字段（记录触发审核的原因）
    cursor.execute("ALTER TABLE check_ins ADD COLUMN review_reason TEXT DEFAULT NULL")
    
    conn.commit()
    print("数据库迁移完成：V4.0 -> V5.0")


def run_migrations():
    """执行所有数据库迁移"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        migrate_v1_to_v2(cursor, conn)
        migrate_v2_to_v3(cursor, conn)
        migrate_v3_to_v4(cursor, conn)
        migrate_v4_to_v5(cursor, conn)
        ensure_likes_table(cursor, conn)
    finally:
        conn.close()
