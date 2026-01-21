"""点赞数据访问层"""
import sqlite3
from typing import List, Tuple

from ..connection import get_db


def add(checkin_id: int, ip_address: str) -> Tuple[bool, int, str]:
    """给记录点赞
    
    Args:
        checkin_id: 记录ID
        ip_address: 点赞者IP
    
    Returns:
        (是否成功, 当前点赞数, 消息)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        try:
            # 检查记录是否存在
            cursor.execute("SELECT love FROM check_ins WHERE id = ?", (checkin_id,))
            row = cursor.fetchone()
            if not row:
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
            
            # 获取最新点赞数
            cursor.execute("SELECT love FROM check_ins WHERE id = ?", (checkin_id,))
            new_love = cursor.fetchone()[0]
            
            return True, new_love, "点赞成功"
            
        except sqlite3.IntegrityError:
            # 重复点赞
            cursor.execute("SELECT love FROM check_ins WHERE id = ?", (checkin_id,))
            current_love = cursor.fetchone()[0]
            return False, current_love, "你已经点过赞了"
        except Exception as e:
            return False, 0, f"点赞失败: {str(e)}"


def check(checkin_id: int, ip_address: str) -> bool:
    """检查是否已点赞
    
    Args:
        checkin_id: 记录ID
        ip_address: IP地址
    
    Returns:
        是否已点赞
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM likes 
            WHERE checkin_id = ? AND ip_address = ?
        """, (checkin_id, ip_address))
        
        return cursor.fetchone() is not None


def get_liked_ids(ip_address: str) -> List[int]:
    """获取某IP已点赞的所有记录ID
    
    Args:
        ip_address: IP地址
    
    Returns:
        已点赞的记录ID列表
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT checkin_id FROM likes 
            WHERE ip_address = ?
        """, (ip_address,))
        
        return [row[0] for row in cursor.fetchall()]
