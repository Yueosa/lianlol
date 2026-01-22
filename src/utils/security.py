"""
安全防护工具模块
- IP 地理位置检测与封锁
- 请求频率限制
- 黑名单管理
"""

import time
import re
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict
from collections import defaultdict
from functools import lru_cache

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 黑名单文件
BLACKLIST_FILE = DATA_DIR / "blacklist.txt"
GEOIP_DB_FILE = DATA_DIR / "GeoLite2-Country.mmdb"

# ============ IP 黑名单管理 ============

def load_blacklist() -> set:
    """加载 IP 黑名单"""
    if not BLACKLIST_FILE.exists():
        return set()
    
    blacklist = set()
    with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                blacklist.add(line)
    return blacklist


def add_to_blacklist(ip: str) -> None:
    """添加 IP 到黑名单"""
    with open(BLACKLIST_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{ip}\n")


def is_blacklisted(ip: str) -> bool:
    """检查 IP 是否在黑名单中"""
    blacklist = load_blacklist()
    return ip in blacklist


# ============ IP 地理位置检测 ============

# GeoIP 数据库读取器（懒加载）
_geoip_reader = None

def _get_geoip_reader():
    """获取 GeoIP 数据库读取器"""
    global _geoip_reader
    
    if _geoip_reader is not None:
        return _geoip_reader
    
    if not GEOIP_DB_FILE.exists():
        return None
    
    try:
        import geoip2.database
        _geoip_reader = geoip2.database.Reader(str(GEOIP_DB_FILE))
        return _geoip_reader
    except Exception:
        return None


def get_country_code(ip: str) -> Optional[str]:
    """
    获取 IP 所属国家代码
    
    Returns:
        国家代码（如 'CN', 'US', 'NL'）或 None
    """
    # 跳过本地 IP
    if ip in ('127.0.0.1', 'localhost', '::1') or ip.startswith('192.168.') or ip.startswith('10.'):
        return 'LOCAL'
    
    reader = _get_geoip_reader()
    if reader is None:
        # 没有数据库，使用备用方案：中国 IP 段检测
        return _check_china_ip_range(ip)
    
    try:
        response = reader.country(ip)
        return response.country.iso_code
    except Exception:
        return None


def ip_to_int(ip: str) -> int:
    """将 IP 地址转换为整数"""
    try:
        parts = ip.split('.')
        return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
    except Exception:
        return 0


# 中国 IP 段（简化版，覆盖主要段）
# 来源：APNIC 分配给中国的主要 IP 段
# 使用懒加载避免启动时计算
_CHINA_IP_RANGES = None

def _get_china_ip_ranges():
    """获取中国 IP 段列表（懒加载）"""
    global _CHINA_IP_RANGES
    if _CHINA_IP_RANGES is not None:
        return _CHINA_IP_RANGES
    
    _CHINA_IP_RANGES = [
        # 格式：(起始IP整数, 结束IP整数)
        # 这里列出一些主要的中国 IP 段
        (ip_to_int("1.0.1.0"), ip_to_int("1.0.3.255")),
        (ip_to_int("1.0.8.0"), ip_to_int("1.0.15.255")),
        (ip_to_int("1.0.32.0"), ip_to_int("1.0.63.255")),
        (ip_to_int("1.1.0.0"), ip_to_int("1.1.0.255")),
        (ip_to_int("1.1.2.0"), ip_to_int("1.1.63.255")),
        (ip_to_int("1.2.0.0"), ip_to_int("1.2.255.255")),
        (ip_to_int("1.4.1.0"), ip_to_int("1.4.127.255")),
        (ip_to_int("1.8.0.0"), ip_to_int("1.8.255.255")),
        (ip_to_int("1.12.0.0"), ip_to_int("1.15.255.255")),
        (ip_to_int("1.24.0.0"), ip_to_int("1.31.255.255")),
        (ip_to_int("1.45.0.0"), ip_to_int("1.45.255.255")),
        (ip_to_int("1.48.0.0"), ip_to_int("1.51.255.255")),
        (ip_to_int("1.56.0.0"), ip_to_int("1.63.255.255")),
        (ip_to_int("1.68.0.0"), ip_to_int("1.71.255.255")),
        (ip_to_int("1.80.0.0"), ip_to_int("1.95.255.255")),
        (ip_to_int("1.116.0.0"), ip_to_int("1.119.255.255")),
        (ip_to_int("1.180.0.0"), ip_to_int("1.183.255.255")),
        (ip_to_int("1.188.0.0"), ip_to_int("1.191.255.255")),
        (ip_to_int("1.192.0.0"), ip_to_int("1.207.255.255")),
        (ip_to_int("14.0.0.0"), ip_to_int("14.255.255.255")),
        (ip_to_int("27.0.0.0"), ip_to_int("27.255.255.255")),
        (ip_to_int("36.0.0.0"), ip_to_int("36.255.255.255")),
        (ip_to_int("39.0.0.0"), ip_to_int("39.255.255.255")),
        (ip_to_int("42.0.0.0"), ip_to_int("42.255.255.255")),
        (ip_to_int("49.0.0.0"), ip_to_int("49.255.255.255")),
        (ip_to_int("58.0.0.0"), ip_to_int("58.255.255.255")),
        (ip_to_int("59.0.0.0"), ip_to_int("59.255.255.255")),
        (ip_to_int("60.0.0.0"), ip_to_int("60.255.255.255")),
    (ip_to_int("61.0.0.0"), ip_to_int("61.255.255.255")),
    (ip_to_int("101.0.0.0"), ip_to_int("101.255.255.255")),
    (ip_to_int("103.0.0.0"), ip_to_int("103.255.255.255")),
    (ip_to_int("106.0.0.0"), ip_to_int("106.255.255.255")),
    (ip_to_int("110.0.0.0"), ip_to_int("110.255.255.255")),
    (ip_to_int("111.0.0.0"), ip_to_int("111.255.255.255")),
    (ip_to_int("112.0.0.0"), ip_to_int("112.255.255.255")),
    (ip_to_int("113.0.0.0"), ip_to_int("113.255.255.255")),
    (ip_to_int("114.0.0.0"), ip_to_int("114.255.255.255")),
    (ip_to_int("115.0.0.0"), ip_to_int("115.255.255.255")),
    (ip_to_int("116.0.0.0"), ip_to_int("116.255.255.255")),
    (ip_to_int("117.0.0.0"), ip_to_int("117.255.255.255")),
    (ip_to_int("118.0.0.0"), ip_to_int("118.255.255.255")),
    (ip_to_int("119.0.0.0"), ip_to_int("119.255.255.255")),
    (ip_to_int("120.0.0.0"), ip_to_int("120.255.255.255")),
    (ip_to_int("121.0.0.0"), ip_to_int("121.255.255.255")),
    (ip_to_int("122.0.0.0"), ip_to_int("122.255.255.255")),
    (ip_to_int("123.0.0.0"), ip_to_int("123.255.255.255")),
    (ip_to_int("124.0.0.0"), ip_to_int("124.255.255.255")),
    (ip_to_int("125.0.0.0"), ip_to_int("125.255.255.255")),
    (ip_to_int("126.0.0.0"), ip_to_int("126.255.255.255")),
    (ip_to_int("139.0.0.0"), ip_to_int("139.255.255.255")),
    (ip_to_int("140.0.0.0"), ip_to_int("140.255.255.255")),
    (ip_to_int("144.0.0.0"), ip_to_int("144.255.255.255")),
    (ip_to_int("150.0.0.0"), ip_to_int("150.255.255.255")),
    (ip_to_int("153.0.0.0"), ip_to_int("153.255.255.255")),
    (ip_to_int("157.0.0.0"), ip_to_int("157.255.255.255")),
    (ip_to_int("159.0.0.0"), ip_to_int("159.255.255.255")),
    (ip_to_int("163.0.0.0"), ip_to_int("163.255.255.255")),
    (ip_to_int("171.0.0.0"), ip_to_int("171.255.255.255")),
    (ip_to_int("175.0.0.0"), ip_to_int("175.255.255.255")),
    (ip_to_int("180.0.0.0"), ip_to_int("180.255.255.255")),
    (ip_to_int("182.0.0.0"), ip_to_int("182.255.255.255")),
    (ip_to_int("183.0.0.0"), ip_to_int("183.255.255.255")),
    (ip_to_int("202.0.0.0"), ip_to_int("202.255.255.255")),
    (ip_to_int("203.0.0.0"), ip_to_int("203.255.255.255")),
    (ip_to_int("210.0.0.0"), ip_to_int("210.255.255.255")),
    (ip_to_int("211.0.0.0"), ip_to_int("211.255.255.255")),
    (ip_to_int("218.0.0.0"), ip_to_int("218.255.255.255")),
    (ip_to_int("219.0.0.0"), ip_to_int("219.255.255.255")),
    (ip_to_int("220.0.0.0"), ip_to_int("220.255.255.255")),
        (ip_to_int("221.0.0.0"), ip_to_int("221.255.255.255")),
        (ip_to_int("222.0.0.0"), ip_to_int("222.255.255.255")),
        (ip_to_int("223.0.0.0"), ip_to_int("223.255.255.255")),
    ]
    return _CHINA_IP_RANGES


def _check_china_ip_range(ip: str) -> Optional[str]:
    """使用 IP 段检查是否为中国 IP（备用方案）"""
    ip_int = ip_to_int(ip)
    if ip_int == 0:
        return None
    
    china_ranges = _get_china_ip_ranges()
    for start, end in china_ranges:
        if start <= ip_int <= end:
            return 'CN'
    
    return None


def is_china_ip(ip: str) -> bool:
    """检查是否为中国大陆 IP"""
    country = get_country_code(ip)
    return country == 'CN'


def is_blocked_country(ip: str) -> Tuple[bool, Optional[str]]:
    """
    检查 IP 是否来自被封锁的国家
    
    Returns:
        (是否封锁, 国家代码)
    """
    country = get_country_code(ip)
    
    # 封锁中国大陆 IP
    blocked_countries = {'CN'}
    
    if country in blocked_countries:
        return True, country
    
    return False, country


# ============ 请求频率限制 ============

# 内存中的请求记录 {ip: [(timestamp, action), ...]}
_request_history: Dict[str, list] = defaultdict(list)

# 配置
RATE_LIMIT_WINDOW = 60  # 时间窗口（秒）
RATE_LIMIT_MAX_REQUESTS = 10  # 窗口内最大请求数（写入操作）
RATE_LIMIT_BAN_DURATION = 300  # 超限后封禁时长（秒）

# 临时封禁记录 {ip: ban_until_timestamp}
_temp_bans: Dict[str, float] = {}


def check_rate_limit(ip: str, action: str = "write") -> Tuple[bool, str]:
    """
    检查请求频率限制
    
    Args:
        ip: 客户端 IP
        action: 操作类型 ("write" 需要限制, "read" 不限制)
    
    Returns:
        (是否允许, 错误信息)
    """
    if action != "write":
        return True, ""
    
    now = time.time()
    
    # 检查是否在临时封禁中
    if ip in _temp_bans:
        if now < _temp_bans[ip]:
            remaining = int(_temp_bans[ip] - now)
            return False, f"请求过于频繁，请 {remaining} 秒后再试"
        else:
            del _temp_bans[ip]
    
    # 清理过期记录
    _request_history[ip] = [
        (ts, act) for ts, act in _request_history[ip]
        if now - ts < RATE_LIMIT_WINDOW
    ]
    
    # 统计窗口内的写入请求数
    write_count = sum(1 for ts, act in _request_history[ip] if act == "write")
    
    if write_count >= RATE_LIMIT_MAX_REQUESTS:
        # 超限，临时封禁
        _temp_bans[ip] = now + RATE_LIMIT_BAN_DURATION
        return False, f"请求过于频繁，已被临时限制 {RATE_LIMIT_BAN_DURATION} 秒"
    
    # 记录本次请求
    _request_history[ip].append((now, action))
    
    return True, ""


# ============ 内容哈希去重 ============

# 最近提交内容的哈希 {hash: timestamp}
_content_hashes: Dict[str, float] = {}
DUPLICATE_WINDOW = 300  # 5分钟内不允许重复内容


def check_duplicate_content(content: str) -> Tuple[bool, str]:
    """
    检查是否为重复内容
    
    Returns:
        (是否允许, 错误信息)
    """
    now = time.time()
    
    # 清理过期哈希
    expired = [h for h, ts in _content_hashes.items() if now - ts > DUPLICATE_WINDOW]
    for h in expired:
        del _content_hashes[h]
    
    # 计算内容哈希
    content_hash = hashlib.md5(content.strip().encode()).hexdigest()
    
    if content_hash in _content_hashes:
        return False, "内容重复，请勿短时间内重复提交相同内容"
    
    # 记录哈希
    _content_hashes[content_hash] = now
    
    return True, ""


# ============ 蜜罐检测 ============

def check_honeypot(honeypot_value: Optional[str], form_timestamp: Optional[str]) -> Tuple[bool, str]:
    """
    检查蜜罐字段和表单时间戳
    
    Args:
        honeypot_value: 蜜罐字段值（应为空）
        form_timestamp: 表单加载时间戳
    
    Returns:
        (是否通过, 错误信息)
    """
    # 检查蜜罐字段（正常用户不会填写）
    if honeypot_value and honeypot_value.strip():
        return False, "检测到异常请求"
    
    # 检查表单填写时间
    if form_timestamp:
        try:
            load_time = float(form_timestamp)
            elapsed = time.time() - load_time
            
            # 填写时间小于 3 秒，可能是机器人
            if elapsed < 3:
                return False, "提交过快，请稍后再试"
            
            # 表单超过 1 小时，可能是重放攻击
            if elapsed > 3600:
                return False, "表单已过期，请刷新页面"
                
        except (ValueError, TypeError):
            pass  # 时间戳无效，忽略检查
    
    return True, ""


# ============ 综合安全检查 ============

def security_check(
    ip: str,
    action: str = "read",
    content: Optional[str] = None,
    honeypot_value: Optional[str] = None,
    form_timestamp: Optional[str] = None
) -> Tuple[bool, int, str]:
    """
    综合安全检查
    
    Args:
        ip: 客户端 IP
        action: 操作类型 ("read" 或 "write")
        content: 提交内容（仅写入时需要）
        honeypot_value: 蜜罐字段值
        form_timestamp: 表单加载时间戳
    
    Returns:
        (是否通过, HTTP状态码, 错误信息)
    """
    # 1. 检查黑名单
    if is_blacklisted(ip):
        return False, 403, "Access Denied"
    
    # 2. 检查国家/地区封锁
    is_blocked, country = is_blocked_country(ip)
    if is_blocked:
        # 451: Unavailable For Legal Reasons (讽刺性状态码)
        return False, 451, f"此服务在您所在的地区 ({country}) 不可用"
    
    # 以下检查仅针对写入操作
    if action == "write":
        # 3. 检查频率限制
        allowed, error = check_rate_limit(ip, action)
        if not allowed:
            return False, 429, error
        
        # 4. 检查蜜罐
        allowed, error = check_honeypot(honeypot_value, form_timestamp)
        if not allowed:
            return False, 400, error
        
        # 5. 检查重复内容
        if content:
            allowed, error = check_duplicate_content(content)
            if not allowed:
                return False, 400, error
    
    return True, 200, ""
