#!/usr/bin/env python3
"""
测试数据生成工具
用于快速向数据库插入大量测试数据，方便测试筛选/搜索功能
"""

import argparse
import sqlite3
import json
import random
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 默认数据库路径
DEFAULT_DB_PATH = PROJECT_ROOT / "src" / "db" / "lol.db"

# ANSI 颜色码
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def color(text, c):
    """给文本添加颜色"""
    return f"{c}{text}{Colors.ENDC}"


# ==================== 随机数据词库 ====================

AVATARS = [
    "🥰", "😍", "🥵", "🥺", "🤤", "😻", "💦", "👅", "🍆", "🍑",
    "💋", "😈", "😏", "🔥", "💕", "💓", "🫦", "👄", "😋", "🤭",
    "😘", "🥴", "😩", "💗", "❤️", "🧡", "💛", "💚", "💙", "💜"
]

NICKNAME_PREFIXES = [
    "可爱的", "快乐的", "温柔的", "活泼的", "调皮的", "害羞的",
    "神秘的", "浪漫的", "甜蜜的", "迷人的", "性感的", "优雅的",
    "狂野的", "寂寞的", "热情的", "冷艳的", "萌萌的", "妖娆的"
]

NICKNAME_SUFFIXES = [
    "小猫咪", "小兔子", "小狐狸", "小妖精", "小仙女", "小公主",
    "小宝贝", "小甜心", "小可爱", "小天使", "小妖女", "小魔女",
    "喵喵", "兔兔", "狐狸", "精灵", "仙子", "美人",
    "User", "Guest", "Lover", "Angel", "Devil", "Baby"
]

CONTENT_TEMPLATES = [
    "今天看了一部超棒的片子，推荐给大家：{link}",
    "这个本子太香了 {link} 必看！",
    "刚才的体验：{emoji} {emoji} {emoji}",
    "今天的心情：{feeling}，素材评分：{score}分",
    "新发现的网站：{link}",
    "这个作者的作品都很棒：{author}",
    "时长：{duration}分钟，体验：{experience}",
    "{greeting}！今天又是快乐的一天",
    "推荐一个宝藏：{link}",
    "看完了，{comment}",
    "今天用的是：{material}",
    "心得体会：{thought}",
    "第{count}次打卡，坚持就是胜利！",
    "偶然发现的好东西：{discovery}",
    "{time_of_day}的快乐时光",
]

FEELINGS = ["超爽", "很舒服", "一般般", "不错", "绝了", "太顶了", "爽翻了", "意犹未尽", "还想要"]
EXPERIENCES = ["极致", "完美", "舒适", "满足", "愉悦", "惬意", "销魂", "飘飘欲仙"]
GREETINGS = ["大家好", "嗨", "Hello", "又来了", "我来打卡啦", "今日份快乐"]
COMMENTS = ["意犹未尽", "下次还来", "太棒了", "强烈推荐", "一般般吧", "还不错", "超级推荐"]
MATERIALS = ["日漫", "国漫", "3D", "真人", "小说", "音声", "游戏", "视频", "图片"]
THOUGHTS = ["今天很开心", "满足了", "期待明天", "继续加油", "生活真美好", "快乐无边"]
DISCOVERIES = ["一个宝藏网站", "新的本子作者", "绝版资源", "高清合集", "限定内容"]
TIMES_OF_DAY = ["清晨", "午后", "傍晚", "深夜", "凌晨", "周末", "假期"]

FAKE_LINKS = [
    "https://example.com/video/12345",
    "https://sample-site.net/content/abc",
    "https://doujin-site.com/work/67890",
    "https://anime-source.org/ep/001",
    "https://gallery.example/album/xyz",
    "https://resource-hub.io/item/999",
    "https://collection.site/set/111",
]

FAKE_AUTHORS = [
    "月野うさぎ", "桜井あゆみ", "花音", "水無月", "雪乃",
    "Artist_A", "Creator_B", "Master_C", "Studio_X", "Circle_Y"
]

EMAIL_DOMAINS = ["gmail.com", "qq.com", "163.com", "outlook.com", "hotmail.com", "yahoo.com"]
QQ_PREFIXES = ["10", "12", "15", "18", "20", "28", "31", "50", "66", "88"]


def generate_nickname():
    """生成随机昵称"""
    style = random.choice(['cn', 'cn', 'simple', 'number'])
    
    if style == 'cn':
        return random.choice(NICKNAME_PREFIXES) + random.choice(NICKNAME_SUFFIXES)
    elif style == 'simple':
        return random.choice(NICKNAME_SUFFIXES) + str(random.randint(1, 999))
    else:
        return f"用户{random.randint(1000, 9999)}"


def generate_content():
    """生成随机内容"""
    template = random.choice(CONTENT_TEMPLATES)
    
    content = template.format(
        link=random.choice(FAKE_LINKS),
        emoji=random.choice(AVATARS),
        feeling=random.choice(FEELINGS),
        score=random.randint(6, 10),
        author=random.choice(FAKE_AUTHORS),
        duration=random.randint(5, 60),
        experience=random.choice(EXPERIENCES),
        greeting=random.choice(GREETINGS),
        comment=random.choice(COMMENTS),
        material=random.choice(MATERIALS),
        thought=random.choice(THOUGHTS),
        count=random.randint(1, 100),
        discovery=random.choice(DISCOVERIES),
        time_of_day=random.choice(TIMES_OF_DAY),
    )
    
    # 有概率添加额外内容
    if random.random() < 0.3:
        content += f"\n\n{random.choice(THOUGHTS)}"
    
    return content


def generate_email():
    """生成随机邮箱"""
    name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(6, 12)))
    domain = random.choice(EMAIL_DOMAINS)
    return f"{name}@{domain}"


def generate_qq():
    """生成随机QQ号"""
    prefix = random.choice(QQ_PREFIXES)
    suffix = ''.join(random.choices('0123456789', k=random.randint(6, 8)))
    return prefix + suffix


def generate_url():
    """生成随机URL"""
    return random.choice(FAKE_LINKS)


def generate_datetime(days_range):
    """生成指定天数范围内的随机时间"""
    now = datetime.now()
    random_days = random.uniform(0, days_range)
    random_time = now - timedelta(days=random_days)
    return random_time.strftime('%Y-%m-%d %H:%M:%S')


def create_checkin(days_range, contact_rate):
    """创建一条随机打卡记录"""
    checkin = {
        'content': generate_content(),
        'media_files': '[]',
        'created_at': generate_datetime(days_range),
        'ip_address': f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}",
        'nickname': generate_nickname(),
        'email': generate_email() if random.random() < contact_rate else None,
        'qq': generate_qq() if random.random() < contact_rate else None,
        'url': generate_url() if random.random() < contact_rate * 0.5 else None,
        'avatar': random.choice(AVATARS),
        'love': 0,  # V3.0: 点赞数默认为0
    }
    return checkin


def insert_checkins(db_path, count, days_range, contact_rate, clear_first):
    """批量插入打卡记录"""
    
    # 检查数据库
    if not os.path.exists(db_path):
        print(color(f"错误: 数据库文件不存在: {db_path}", Colors.RED))
        print("请先运行一次服务器以创建数据库")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 清空数据
    if clear_first:
        cursor.execute("SELECT COUNT(*) FROM check_ins")
        old_count = cursor.fetchone()[0]
        cursor.execute("DELETE FROM check_ins")
        print(color(f"🗑️  已清空 {old_count} 条旧记录", Colors.YELLOW))
    
    print(color(f"\n🌱 开始生成 {count} 条测试数据...\n", Colors.HEADER))
    
    # 批量插入
    inserted = 0
    batch_size = 100
    
    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        batch = []
        
        for _ in range(batch_count):
            checkin = create_checkin(days_range, contact_rate)
            batch.append((
                checkin['content'],
                checkin['media_files'],
                checkin['created_at'],
                checkin['ip_address'],
                checkin['nickname'],
                checkin['email'],
                checkin['qq'],
                checkin['url'],
                checkin['avatar'],
                checkin['love'],
            ))
        
        cursor.executemany("""
            INSERT INTO check_ins (content, media_files, created_at, ip_address, nickname, email, qq, url, avatar, love)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        
        inserted += batch_count
        
        # 进度条
        progress = inserted / count
        bar_width = 40
        filled = int(bar_width * progress)
        bar = '█' * filled + '░' * (bar_width - filled)
        percent = progress * 100
        print(f"\r  [{bar}] {percent:.1f}% ({inserted}/{count})", end='', flush=True)
    
    conn.commit()
    print()  # 换行
    
    # 统计信息
    cursor.execute("SELECT COUNT(*) FROM check_ins")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE email IS NOT NULL")
    with_email = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE qq IS NOT NULL")
    with_qq = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE url IS NOT NULL")
    with_url = cursor.fetchone()[0]
    
    conn.close()
    
    print(color("\n✅ 数据生成完成！\n", Colors.GREEN))
    print(f"  {color('新增记录:', Colors.CYAN)} {inserted}")
    print(f"  {color('总记录数:', Colors.CYAN)} {total}")
    print(f"  {color('有邮箱:', Colors.CYAN)} {with_email}")
    print(f"  {color('有QQ:', Colors.CYAN)} {with_qq}")
    print(f"  {color('有链接:', Colors.CYAN)} {with_url}")
    print(f"  {color('时间范围:', Colors.CYAN)} 过去 {days_range} 天")
    print()


def main():
    parser = argparse.ArgumentParser(
        description=color("🌱 撸了吗 - 测试数据生成工具", Colors.HEADER),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python db_seed.py --count 50              # 插入50条随机数据
  python db_seed.py --count 100 --days 7    # 插入100条，时间分布在过去7天
  python db_seed.py --count 50 --contact-rate 0.5   # 50%概率生成联系方式
  python db_seed.py --count 100 --clear-first       # 清空后重新生成
        """
    )
    
    parser.add_argument('--db', default=str(DEFAULT_DB_PATH),
                        help='数据库文件路径')
    parser.add_argument('--count', '-n', type=int, default=50,
                        help='生成记录数量 (默认: 50)')
    parser.add_argument('--days', '-d', type=int, default=30,
                        help='时间分布范围，过去N天 (默认: 30)')
    parser.add_argument('--contact-rate', '-c', type=float, default=0.3,
                        help='联系方式生成概率 0-1 (默认: 0.3)')
    parser.add_argument('--clear-first', action='store_true',
                        help='插入前先清空所有数据')
    
    args = parser.parse_args()
    
    # 参数验证
    if args.count < 1:
        print(color("错误: count 必须大于 0", Colors.RED))
        sys.exit(1)
    
    if args.days < 1:
        print(color("错误: days 必须大于 0", Colors.RED))
        sys.exit(1)
    
    if not 0 <= args.contact_rate <= 1:
        print(color("错误: contact-rate 必须在 0-1 之间", Colors.RED))
        sys.exit(1)
    
    insert_checkins(
        db_path=args.db,
        count=args.count,
        days_range=args.days,
        contact_rate=args.contact_rate,
        clear_first=args.clear_first
    )


if __name__ == '__main__':
    main()
