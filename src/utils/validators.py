"""数据验证工具函数"""
import re
from typing import Optional, Tuple


def validate_email(email: Optional[str]) -> Tuple[bool, str]:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址（可选）
    
    Returns:
        (是否有效, 错误信息)
    """
    if not email or email.strip() == "":
        return True, ""  # 邮箱是可选的
    
    email = email.strip()
    
    # 简单的邮箱格式验证正则
    # 符合大部分邮箱格式，遵循 RFC 5322 简化版
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "邮箱格式不正确"
    
    if len(email) > 254:  # RFC 5321 规定邮箱最大长度
        return False, "邮箱地址过长"
    
    return True, ""


def validate_url(url: Optional[str]) -> Tuple[bool, str]:
    """
    验证 URL 格式
    
    Args:
        url: URL 地址（可选）
    
    Returns:
        (是否有效, 错误信息)
    """
    if not url or url.strip() == "":
        return True, ""  # URL 是可选的
    
    url = url.strip()
    
    # 检查协议（只支持 http 和 https）
    if not url.startswith(('http://', 'https://')):
        return False, "URL 必须以 http:// 或 https:// 开头"
    
    # URL 格式验证正则
    pattern = r'^https?://[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*(/.*)?$'
    
    if not re.match(pattern, url):
        return False, "URL 格式不正确"
    
    if len(url) > 2048:  # 大部分浏览器支持的最大 URL 长度
        return False, "URL 地址过长"
    
    # TODO: 未来可能需要添加 URL 黑名单检查或域名白名单验证
    # TODO: 可以考虑检查 URL 是否可访问（发送 HEAD 请求）
    
    return True, ""


def validate_qq(qq: Optional[str]) -> Tuple[bool, str]:
    """
    验证 QQ 号格式
    
    Args:
        qq: QQ 号（可选）
    
    Returns:
        (是否有效, 错误信息)
    """
    if not qq or qq.strip() == "":
        return True, ""  # QQ 号是可选的
    
    qq = qq.strip()
    
    # QQ 号必须是 5-11 位纯数字
    if not qq.isdigit():
        return False, "QQ 号必须是纯数字"
    
    if len(qq) < 5 or len(qq) > 11:
        return False, "QQ 号长度必须在 5-11 位之间"
    
    return True, ""


def validate_nickname(nickname: Optional[str]) -> Tuple[bool, str]:
    """
    验证昵称格式
    
    Args:
        nickname: 昵称
    
    Returns:
        (是否有效, 错误信息)
    """
    if not nickname:
        # 如果未提供昵称，使用默认值（在调用方处理）
        return True, ""
    
    nickname = nickname.strip()
    
    if len(nickname) == 0:
        return True, ""  # 空字符串将使用默认值
    
    if len(nickname) > 20:
        return False, "昵称长度不能超过 20 个字符"
    
    if len(nickname) < 1:
        return False, "昵称不能为空"
    
    # 禁止某些特殊字符（可根据需要调整）
    forbidden_chars = ['<', '>', '&', '"', "'", '\\', '/', '\n', '\r', '\t']
    for char in forbidden_chars:
        if char in nickname:
            return False, f"昵称不能包含特殊字符: {char}"
    
    return True, ""


def validate_emoji(emoji: Optional[str]) -> Tuple[bool, str]:
    """
    验证是否为有效的单个 emoji
    
    Args:
        emoji: emoji 字符
    
    Returns:
        (是否有效, 错误信息)
    """
    if not emoji:
        # 如果未提供 emoji，使用默认值（在调用方处理）
        return True, ""
    
    if len(emoji) == 0:
        return True, ""  # 空字符串将使用默认值
    
    # 简单检查：emoji 的 Unicode 范围
    # 这是一个简化的检查，涵盖大部分常用 emoji
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 表情符号
        "\U0001F300-\U0001F5FF"  # 符号和象形文字
        "\U0001F680-\U0001F6FF"  # 交通和地图符号
        "\U0001F700-\U0001F77F"  # 炼金术符号
        "\U0001F780-\U0001F7FF"  # 几何形状扩展
        "\U0001F800-\U0001F8FF"  # 补充箭头-C
        "\U0001F900-\U0001F9FF"  # 补充符号和象形文字
        "\U0001FA00-\U0001FA6F"  # 国际象棋符号
        "\U0001FA70-\U0001FAFF"  # 符号和象形文字扩展-A
        "\U00002702-\U000027B0"  # 装饰符号
        "\U000024C2-\U0001F251"  # 封闭字母数字补充
        "]+",
        flags=re.UNICODE
    )
    
    if not emoji_pattern.fullmatch(emoji):
        return False, "头像必须是一个有效的 emoji 表情"
    
    # 检查长度，确保是单个 emoji（某些 emoji 可能由多个 Unicode 字符组成）
    # 这里简单限制为不超过 10 个字符（处理组合 emoji）
    if len(emoji) > 10:
        return False, "头像只能是一个 emoji 表情"
    
    return True, ""


def validate_content(content: str) -> Tuple[bool, str]:
    """
    验证内容格式
    
    Args:
        content: 打卡内容
    
    Returns:
        (是否有效, 错误信息)
    """
    if not content or content.strip() == "":
        return False, "内容不能为空"
    
    content = content.strip()
    
    if len(content) < 1:
        return False, "内容不能为空"
    
    if len(content) > 10000:  # 限制最大长度
        return False, "内容长度不能超过 10000 个字符"
    
    return True, ""
