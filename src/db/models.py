"""数据模型定义"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class CheckIn:
    """打卡记录模型"""
    id: Optional[int] = None
    content: str = ""
    media_files: str = "[]"  # JSON 字符串，存储文件路径列表
    created_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "media_files": self.media_files,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ip_address": self.ip_address
        }
