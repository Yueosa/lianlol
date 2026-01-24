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
    # VERSION 2.0 新增字段
    nickname: str = "用户0721"
    email: Optional[str] = None
    qq: Optional[str] = None
    url: Optional[str] = None
    avatar: str = "🥰"
    # VERSION 3.0 新增字段
    love: int = 0
    # VERSION 4.0 新增字段
    file_type: str = "media"  # 'media' 或 'archive'
    archive_metadata: Optional[str] = None  # JSON 字符串，存储压缩包元数据
    # VERSION 5.0 新增字段
    approved: bool = True  # 审核状态：True=通过, False=待审
    reviewed_at: Optional[datetime] = None  # 审核时间
    review_reason: Optional[str] = None  # 触发审核的原因
    # 动态计算的显示编号（不存储在数据库）
    display_number: Optional[int] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "display_number": self.display_number,
            "content": self.content,
            "media_files": self.media_files,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ip_address": self.ip_address,
            "nickname": self.nickname,
            "email": self.email,
            "qq": self.qq,
            "url": self.url,
            "avatar": self.avatar,
            "love": self.love,
            "file_type": self.file_type,
            "archive_metadata": self.archive_metadata,
            "approved": self.approved,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_reason": self.review_reason
        }
