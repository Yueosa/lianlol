"""数据库初始化"""
import sqlite3
from .connection import DB_PATH
from .migrations import run_migrations


def create_tables():
    """创建数据库表（V5.0 完整架构）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建 check_ins 表
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
            love INTEGER DEFAULT 0,
            file_type TEXT DEFAULT 'media',
            archive_metadata TEXT DEFAULT NULL,
            approved INTEGER DEFAULT 1,
            reviewed_at DATETIME DEFAULT NULL
        )
    """)
    
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
    conn.close()


def init_db():
    """初始化数据库"""
    create_tables()
    run_migrations()
