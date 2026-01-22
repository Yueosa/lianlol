"""数据验证工具函数"""
import re
import html
from pathlib import Path
from typing import Optional, Tuple


# ============ 垃圾关键词加载 ============

DATA_DIR = Path(__file__).parent.parent / "data"
SPAM_KEYWORDS_FILE = DATA_DIR / "spam_keywords.txt"

_spam_keywords: list = []


def _load_spam_keywords() -> list:
    """加载垃圾关键词列表"""
    global _spam_keywords
    
    if _spam_keywords:
        return _spam_keywords
    
    if not SPAM_KEYWORDS_FILE.exists():
        return []
    
    keywords = []
    with open(SPAM_KEYWORDS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                keywords.append(line.lower())
    
    _spam_keywords = keywords
    return keywords


def reload_spam_keywords() -> None:
    """重新加载垃圾关键词（用于热更新）"""
    global _spam_keywords
    _spam_keywords = []
    _load_spam_keywords()


# ============ XSS 防护 ============

def sanitize_html(text: str) -> str:
    """
    清理文本中的 HTML 特殊字符，防止 XSS 攻击
    
    Args:
        text: 原始文本
    
    Returns:
        转义后的安全文本
    """
    if not text:
        return text
    
    # 使用 html.escape 转义特殊字符
    return html.escape(text, quote=True)


def check_xss_patterns(text: str) -> Tuple[bool, str]:
    """
    检测文本中是否包含 XSS 攻击模式
    
    Args:
        text: 待检测文本
    
    Returns:
        (是否安全, 错误信息)
    """
    if not text:
        return True, ""
    
    text_lower = text.lower()
    
    # 危险的 HTML 标签和属性
    dangerous_patterns = [
        r'<\s*script',
        r'<\s*iframe',
        r'<\s*object',
        r'<\s*embed',
        r'<\s*form',
        r'<\s*input',
        r'<\s*link',
        r'<\s*meta',
        r'<\s*style',
        r'<\s*svg',
        r'<\s*math',
        r'javascript\s*:',
        r'vbscript\s*:',
        r'data\s*:',
        r'on\w+\s*=',  # onclick, onerror, onload 等
        r'expression\s*\(',
        r'url\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower):
            return False, "内容包含不允许的代码"
    
    return True, ""


# ============ SQL 注入防护 ============

def check_sql_injection(text: str) -> Tuple[bool, str]:
    """
    检测文本中是否包含 SQL 注入攻击模式
    
    注意：这是额外的防护层，主要防护已经通过参数化查询实现
    
    Args:
        text: 待检测文本
    
    Returns:
        (是否安全, 错误信息)
    """
    if not text:
        return True, ""
    
    text_lower = text.lower()
    
    # 可疑的 SQL 注入模式
    suspicious_patterns = [
        r"('\s*or\s+'.*'\s*=\s*')",  # ' OR '1'='1
        r'(;\s*drop\s+table)',
        r'(;\s*delete\s+from)',
        r'(;\s*insert\s+into)',
        r'(;\s*update\s+.*\s+set)',
        r'(union\s+select)',
        r'(union\s+all\s+select)',
        r'(--\s*$)',  # SQL 注释
        r'(/\*.*\*/)',  # SQL 块注释
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower):
            return False, "内容包含不允许的字符序列"
    
    return True, ""


# ============ 垃圾内容检测 ============

def check_spam_content(text: str) -> Tuple[bool, str]:
    """
    检测文本是否包含垃圾/敏感关键词
    
    Args:
        text: 待检测文本
    
    Returns:
        (是否通过, 错误信息)
    """
    if not text:
        return True, ""
    
    text_lower = text.lower()
    keywords = _load_spam_keywords()
    
    for keyword in keywords:
        if keyword in text_lower:
            return False, "内容包含不允许的词汇"
    
    return True, ""


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
    
    # 检测垃圾昵称模式
    is_spam, msg = check_spam_nickname(nickname)
    if is_spam:
        return False, msg
    
    return True, ""


# ============ 垃圾昵称检测 ============

# 垃圾昵称模式（正则表达式）
SPAM_NICKNAME_PATTERNS = [
    r'爱国青年\d*',
    r'文明使者\d*',
    r'法治宣传员\d*',
    r'新时代青年\d*',
    r'网络安全守护者\d*',
    r'价值观践行者\d*',
    r'诚信公民\d*',
    r'正能量传播者\d*',
    r'友善网友\d*',
    r'守法公民\d*',
    r'网络文明志愿者\d*',
    r'社会主义.*践行者\d*',
    r'中国好网民\d*',
    r'核心价值观.*\d*',
    r'网络卫士\d*',
    r'普法.*\d*',
]


def check_spam_nickname(nickname: str) -> Tuple[bool, str]:
    """
    检测是否为垃圾昵称
    
    Args:
        nickname: 昵称
    
    Returns:
        (是否是垃圾, 错误信息)
    """
    if not nickname:
        return False, ""
    
    for pattern in SPAM_NICKNAME_PATTERNS:
        if re.search(pattern, nickname):
            return True, "昵称不可用"
    
    return False, ""


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
    
    # 检查 XSS 攻击模式
    is_safe, error = check_xss_patterns(content)
    if not is_safe:
        return False, error
    
    # 检查 SQL 注入模式
    is_safe, error = check_sql_injection(content)
    if not is_safe:
        return False, error
    
    # 检查垃圾内容
    is_clean, error = check_spam_content(content)
    if not is_clean:
        return False, error
    
    return True, ""


def validate_all_fields(
    content: str,
    nickname: Optional[str] = None,
    email: Optional[str] = None,
    qq: Optional[str] = None,
    url: Optional[str] = None
) -> Tuple[bool, str]:
    """
    综合验证所有字段的安全性
    
    Args:
        content: 内容
        nickname: 昵称
        email: 邮箱
        qq: QQ号
        url: 链接
    
    Returns:
        (是否通过, 错误信息)
    """
    # 检查所有字段的 XSS
    for field_name, field_value in [
        ("内容", content),
        ("昵称", nickname),
        ("邮箱", email),
        ("QQ", qq),
        ("链接", url)
    ]:
        if field_value:
            is_safe, _ = check_xss_patterns(field_value)
            if not is_safe:
                return False, f"{field_name}包含不允许的内容"
            
            is_safe, _ = check_sql_injection(field_value)
            if not is_safe:
                return False, f"{field_name}包含不允许的内容"
    
    # 检查垃圾内容（仅对 content 和 nickname）
    for field_name, field_value in [("内容", content), ("昵称", nickname)]:
        if field_value:
            is_clean, _ = check_spam_content(field_value)
            if not is_clean:
                return False, f"{field_name}包含不允许的词汇"
    
    return True, ""
