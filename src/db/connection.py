"""数据库连接管理"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

# 数据库路径
DB_PATH = Path(__file__).parent / "lol.db"

# 当前数据库版本
DB_VERSION = "3.0"


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """数据库连接上下文管理器
    
    用法:
        with get_db() as conn:
            cursor = conn.cursor()
            ...
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(sql: str, params: tuple = ()) -> list:
    """执行查询并返回结果"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()


def execute_insert(sql: str, params: tuple = ()) -> int:
    """执行插入并返回最后插入的ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.lastrowid


def execute_update(sql: str, params: tuple = ()) -> int:
    """执行更新并返回影响的行数"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.rowcount
