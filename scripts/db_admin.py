#!/usr/bin/env python3
"""
数据库运维管理工具
用于在服务器命令行环境对 .db 数据库进行运维、修改、更新
"""

import argparse
import sqlite3
import json
import csv
import sys
import os
from datetime import datetime
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


def print_table(headers, rows, max_width=50):
    """打印格式化表格"""
    if not rows:
        print(color("  (无数据)", Colors.DIM))
        return
    
    # 计算列宽
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell is not None else ""
            if len(cell_str) > max_width:
                cell_str = cell_str[:max_width-3] + "..."
            col_widths[i] = max(col_widths[i], len(cell_str))
    
    # 打印表头
    header_line = " │ ".join(color(h.ljust(col_widths[i]), Colors.BOLD) for i, h in enumerate(headers))
    separator = "─┼─".join("─" * w for w in col_widths)
    
    print(f" │ {header_line} │")
    print(f"─┼─{separator}─┼─")
    
    # 打印数据行
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell is not None else ""
            if len(cell_str) > max_width:
                cell_str = cell_str[:max_width-3] + "..."
            cells.append(cell_str.ljust(col_widths[i]))
        print(f" │ {' │ '.join(cells)} │")


def get_connection(db_path):
    """获取数据库连接"""
    if not os.path.exists(db_path):
        print(color(f"错误: 数据库文件不存在: {db_path}", Colors.RED))
        sys.exit(1)
    return sqlite3.connect(db_path)


def cmd_list(args):
    """列出所有记录"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    offset = (args.page - 1) * args.size
    cursor.execute("""
        SELECT id, nickname, avatar, content, love, created_at 
        FROM check_ins 
        ORDER BY id DESC 
        LIMIT ? OFFSET ?
    """, (args.size, offset))
    rows = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM check_ins")
    total = cursor.fetchone()[0]
    total_pages = (total + args.size - 1) // args.size
    
    print(color(f"\n📋 打卡记录列表 (第 {args.page}/{total_pages} 页, 共 {total} 条)\n", Colors.HEADER))
    print_table(["ID", "昵称", "头像", "内容", "❤️", "创建时间"], rows)
    print()
    
    conn.close()


def cmd_show(args):
    """查看单条记录详情"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM check_ins WHERE id = ?", (args.id,))
    row = cursor.fetchone()
    
    if not row:
        print(color(f"错误: 找不到 ID={args.id} 的记录", Colors.RED))
        conn.close()
        return
    
    columns = [desc[0] for desc in cursor.description]
    
    print(color(f"\n📝 记录详情 (ID: {args.id})\n", Colors.HEADER))
    for col, val in zip(columns, row):
        print(f"  {color(col + ':', Colors.CYAN)} {val}")
    print()
    
    conn.close()


def cmd_delete(args):
    """删除指定记录"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    # 先检查是否存在
    cursor.execute("SELECT id FROM check_ins WHERE id = ?", (args.id,))
    if not cursor.fetchone():
        print(color(f"错误: 找不到 ID={args.id} 的记录", Colors.RED))
        conn.close()
        return
    
    if not args.force:
        confirm = input(f"确定要删除 ID={args.id} 的记录吗? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            conn.close()
            return
    
    cursor.execute("DELETE FROM check_ins WHERE id = ?", (args.id,))
    conn.commit()
    print(color(f"✅ 已删除 ID={args.id} 的记录", Colors.GREEN))
    
    conn.close()


def cmd_delete_range(args):
    """删除ID范围内的记录"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE id BETWEEN ? AND ?", 
                   (args.start, args.end))
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(color(f"没有找到 ID 在 {args.start}-{args.end} 范围内的记录", Colors.YELLOW))
        conn.close()
        return
    
    if not args.force:
        confirm = input(f"确定要删除 ID 范围 {args.start}-{args.end} 的 {count} 条记录吗? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            conn.close()
            return
    
    cursor.execute("DELETE FROM check_ins WHERE id BETWEEN ? AND ?", (args.start, args.end))
    conn.commit()
    print(color(f"✅ 已删除 {count} 条记录", Colors.GREEN))
    
    conn.close()


def cmd_update(args):
    """更新记录字段"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    # 检查记录是否存在
    cursor.execute("SELECT * FROM check_ins WHERE id = ?", (args.id,))
    if not cursor.fetchone():
        print(color(f"错误: 找不到 ID={args.id} 的记录", Colors.RED))
        conn.close()
        return
    
    # 构建更新语句
    updates = []
    values = []
    
    if args.content is not None:
        updates.append("content = ?")
        values.append(args.content)
    if args.nickname is not None:
        updates.append("nickname = ?")
        values.append(args.nickname)
    if args.email is not None:
        updates.append("email = ?")
        values.append(args.email if args.email != "" else None)
    if args.qq is not None:
        updates.append("qq = ?")
        values.append(args.qq if args.qq != "" else None)
    if args.url is not None:
        updates.append("url = ?")
        values.append(args.url if args.url != "" else None)
    if args.avatar is not None:
        updates.append("avatar = ?")
        values.append(args.avatar)
    if args.love is not None:
        updates.append("love = ?")
        values.append(args.love)
    
    if not updates:
        print(color("没有指定要更新的字段", Colors.YELLOW))
        conn.close()
        return
    
    values.append(args.id)
    sql = f"UPDATE check_ins SET {', '.join(updates)} WHERE id = ?"
    
    cursor.execute(sql, values)
    conn.commit()
    print(color(f"✅ 已更新 ID={args.id} 的记录", Colors.GREEN))
    
    conn.close()


def cmd_search(args):
    """搜索记录"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    conditions = []
    values = []
    
    if args.content:
        conditions.append("content LIKE ?")
        values.append(f"%{args.content}%")
    if args.nickname:
        conditions.append("nickname LIKE ?")
        values.append(f"%{args.nickname}%")
    if args.email:
        conditions.append("email LIKE ?")
        values.append(f"%{args.email}%")
    if args.qq:
        conditions.append("qq LIKE ?")
        values.append(f"%{args.qq}%")
    
    if not conditions:
        print(color("请指定至少一个搜索条件", Colors.YELLOW))
        conn.close()
        return
    
    sql = f"""
        SELECT id, nickname, avatar, content, love, created_at 
        FROM check_ins 
        WHERE {' AND '.join(conditions)}
        ORDER BY id DESC
        LIMIT 50
    """
    
    cursor.execute(sql, values)
    rows = cursor.fetchall()
    
    print(color(f"\n🔍 搜索结果 (共 {len(rows)} 条)\n", Colors.HEADER))
    print_table(["ID", "昵称", "头像", "内容", "❤️", "创建时间"], rows)
    print()
    
    conn.close()


def cmd_stats(args):
    """显示数据库统计信息"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    print(color("\n📊 数据库统计信息\n", Colors.HEADER))
    
    # 总记录数
    cursor.execute("SELECT COUNT(*) FROM check_ins")
    total = cursor.fetchone()[0]
    print(f"  {color('总记录数:', Colors.CYAN)} {total}")
    
    # 有媒体的记录数
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE media_files != '[]'")
    with_media = cursor.fetchone()[0]
    print(f"  {color('含媒体记录:', Colors.CYAN)} {with_media}")
    
    # 有联系方式的记录数
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE email IS NOT NULL OR qq IS NOT NULL OR url IS NOT NULL")
    with_contact = cursor.fetchone()[0]
    print(f"  {color('有联系方式:', Colors.CYAN)} {with_contact}")
    
    # 点赞统计 (V3.0)
    cursor.execute("SELECT SUM(love), MAX(love), AVG(love) FROM check_ins")
    total_likes, max_likes, avg_likes = cursor.fetchone()
    total_likes = total_likes or 0
    max_likes = max_likes or 0
    avg_likes = avg_likes or 0
    print(f"  {color('总点赞数:', Colors.CYAN)} {total_likes}")
    print(f"  {color('最高点赞:', Colors.CYAN)} {max_likes}")
    print(f"  {color('平均点赞:', Colors.CYAN)} {avg_likes:.1f}")
    
    # 最早/最新记录
    cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM check_ins")
    earliest, latest = cursor.fetchone()
    print(f"  {color('最早记录:', Colors.CYAN)} {earliest or '无'}")
    print(f"  {color('最新记录:', Colors.CYAN)} {latest or '无'}")
    
    # 数据库文件大小
    db_size = os.path.getsize(args.db)
    size_str = f"{db_size / 1024:.1f} KB" if db_size < 1024*1024 else f"{db_size / 1024 / 1024:.2f} MB"
    print(f"  {color('数据库大小:', Colors.CYAN)} {size_str}")
    
    # 点赞最多的记录 TOP 5
    cursor.execute("""
        SELECT id, nickname, love 
        FROM check_ins 
        WHERE love > 0
        ORDER BY love DESC 
        LIMIT 5
    """)
    top_liked = cursor.fetchall()
    if top_liked:
        print(f"\n  {color('点赞最多 TOP 5:', Colors.CYAN)}")
        for record_id, nick, likes in top_liked:
            print(f"    - #{record_id} {nick}: {likes} ❤️")
    
    # 常用昵称 TOP 5
    cursor.execute("""
        SELECT nickname, COUNT(*) as cnt 
        FROM check_ins 
        GROUP BY nickname 
        ORDER BY cnt DESC 
        LIMIT 5
    """)
    top_nicknames = cursor.fetchall()
    print(f"\n  {color('常用昵称 TOP 5:', Colors.CYAN)}")
    for nick, cnt in top_nicknames:
        print(f"    - {nick}: {cnt} 条")
    
    print()
    conn.close()


def cmd_export(args):
    """导出数据"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM check_ins ORDER BY id")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    if args.format == 'json':
        data = [dict(zip(columns, row)) for row in rows]
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    else:  # csv
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
    
    print(color(f"✅ 已导出 {len(rows)} 条记录到 {args.output}", Colors.GREEN))
    conn.close()


def cmd_import(args):
    """从JSON导入数据"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    with open(args.file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print(color("错误: JSON文件格式不正确，应为数组", Colors.RED))
        conn.close()
        return
    
    count = 0
    for item in data:
        try:
            cursor.execute("""
                INSERT INTO check_ins (content, media_files, created_at, ip_address, nickname, email, qq, url, avatar, love)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get('content', ''),
                item.get('media_files', '[]'),
                item.get('created_at'),
                item.get('ip_address'),
                item.get('nickname', '用户0721'),
                item.get('email'),
                item.get('qq'),
                item.get('url'),
                item.get('avatar', '🥰'),
                item.get('love', 0)
            ))
            count += 1
        except Exception as e:
            print(color(f"警告: 导入记录失败: {e}", Colors.YELLOW))
    
    conn.commit()
    print(color(f"✅ 已导入 {count} 条记录", Colors.GREEN))
    conn.close()


def cmd_vacuum(args):
    """压缩优化数据库"""
    conn = get_connection(args.db)
    
    before_size = os.path.getsize(args.db)
    conn.execute("VACUUM")
    conn.close()
    after_size = os.path.getsize(args.db)
    
    saved = before_size - after_size
    print(color(f"✅ 数据库已优化", Colors.GREEN))
    print(f"  优化前: {before_size / 1024:.1f} KB")
    print(f"  优化后: {after_size / 1024:.1f} KB")
    print(f"  节省: {saved / 1024:.1f} KB ({saved * 100 / before_size:.1f}%)")


def cmd_clear(args):
    """清空所有数据"""
    if not args.confirm:
        print(color("⚠️  这是一个危险操作！将删除所有数据！", Colors.RED))
        print("请使用 --confirm 参数确认操作")
        return
    
    confirm = input("最后确认: 输入 'DELETE ALL' 以继续: ")
    if confirm != 'DELETE ALL':
        print("已取消")
        return
    
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM check_ins")
    count = cursor.fetchone()[0]
    
    cursor.execute("DELETE FROM check_ins")
    conn.commit()
    conn.close()
    
    print(color(f"✅ 已删除 {count} 条记录", Colors.GREEN))


def cmd_sql(args):
    """执行原始SQL"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    try:
        cursor.execute(args.query)
        
        if args.query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            if rows:
                columns = [desc[0] for desc in cursor.description]
                print()
                print_table(columns, rows)
                print(f"\n共 {len(rows)} 条结果\n")
            else:
                print(color("查询无结果", Colors.DIM))
        else:
            conn.commit()
            print(color(f"✅ 执行成功，影响 {cursor.rowcount} 行", Colors.GREEN))
    except Exception as e:
        print(color(f"SQL执行错误: {e}", Colors.RED))


# ============ 审核管理命令 ============

def cmd_pending(args):
    """列出待审核记录"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    offset = (args.page - 1) * args.size
    cursor.execute("""
        SELECT id, nickname, content, review_reason, created_at 
        FROM check_ins 
        WHERE approved = 0
        ORDER BY id DESC 
        LIMIT ? OFFSET ?
    """, (args.size, offset))
    rows = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE approved = 0")
    total = cursor.fetchone()[0]
    total_pages = max(1, (total + args.size - 1) // args.size)
    
    print(color(f"\n⏳ 待审核记录 (第 {args.page}/{total_pages} 页, 共 {total} 条)\n", Colors.YELLOW))
    print_table(["ID", "昵称", "内容", "触发原因", "创建时间"], rows)
    print()
    
    conn.close()


def cmd_approve(args):
    """通过审核"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    # 检查记录是否存在
    cursor.execute("SELECT id, nickname, content FROM check_ins WHERE id = ?", (args.id,))
    row = cursor.fetchone()
    
    if not row:
        print(color(f"错误: 找不到 ID={args.id} 的记录", Colors.RED))
        conn.close()
        return
    
    # 显示记录摘要
    content_preview = row[2][:50] + "..." if row[2] and len(row[2]) > 50 else row[2]
    print(f"\n记录摘要: ID={row[0]}, 昵称={row[1]}, 内容={content_preview}")
    
    if not args.force:
        confirm = input(f"确定要通过 ID={args.id} 的审核吗? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            conn.close()
            return
    
    cursor.execute("""
        UPDATE check_ins 
        SET approved = 1, reviewed_at = ? 
        WHERE id = ?
    """, (datetime.now().isoformat(), args.id))
    conn.commit()
    
    print(color(f"✅ 已通过 ID={args.id} 的审核", Colors.GREEN))
    conn.close()


def cmd_reject(args):
    """拒绝并删除记录"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    # 检查记录是否存在
    cursor.execute("SELECT id, nickname, content FROM check_ins WHERE id = ?", (args.id,))
    row = cursor.fetchone()
    
    if not row:
        print(color(f"错误: 找不到 ID={args.id} 的记录", Colors.RED))
        conn.close()
        return
    
    # 显示记录摘要
    content_preview = row[2][:50] + "..." if row[2] and len(row[2]) > 50 else row[2]
    print(f"\n记录摘要: ID={row[0]}, 昵称={row[1]}, 内容={content_preview}")
    
    if not args.force:
        confirm = input(f"确定要拒绝并删除 ID={args.id} 的记录吗? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            conn.close()
            return
    
    cursor.execute("DELETE FROM check_ins WHERE id = ?", (args.id,))
    conn.commit()
    
    print(color(f"✗ 已拒绝并删除 ID={args.id} 的记录", Colors.GREEN))
    conn.close()


def cmd_ban(args):
    """拒绝并加入黑名单"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    # 获取记录和指纹
    cursor.execute("SELECT id, nickname, content, fingerprint FROM check_ins WHERE id = ?", (args.id,))
    row = cursor.fetchone()
    
    if not row:
        print(color(f"错误: 找不到 ID={args.id} 的记录", Colors.RED))
        conn.close()
        return
    
    fingerprint = row[3]
    if not fingerprint:
        print(color("警告: 该记录没有指纹信息，无法加入黑名单", Colors.YELLOW))
        # 仍然删除记录
        if not args.force:
            confirm = input(f"是否仍要删除 ID={args.id} 的记录? (y/N): ")
            if confirm.lower() != 'y':
                print("已取消")
                conn.close()
                return
        cursor.execute("DELETE FROM check_ins WHERE id = ?", (args.id,))
        conn.commit()
        print(color(f"✗ 已删除 ID={args.id} 的记录", Colors.GREEN))
        conn.close()
        return
    
    # 显示记录摘要
    content_preview = row[2][:50] + "..." if row[2] and len(row[2]) > 50 else row[2]
    print(f"\n记录摘要: ID={row[0]}, 昵称={row[1]}, 内容={content_preview}")
    print(f"指纹: {fingerprint}")
    
    if not args.force:
        confirm = input(f"确定要拒绝并将此用户加入黑名单吗? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            conn.close()
            return
    
    # 添加到黑名单文件
    blacklist_path = PROJECT_ROOT / "src" / "data" / "blacklist.txt"
    try:
        with open(blacklist_path, 'a') as f:
            f.write(f"{fingerprint}\n")
        print(color(f"🚫 已将指纹 {fingerprint} 加入黑名单", Colors.YELLOW))
    except Exception as e:
        print(color(f"警告: 无法写入黑名单文件: {e}", Colors.YELLOW))
    
    # 删除记录
    cursor.execute("DELETE FROM check_ins WHERE id = ?", (args.id,))
    conn.commit()
    
    print(color(f"✗ 已拒绝并删除 ID={args.id} 的记录", Colors.GREEN))
    conn.close()


def cmd_batch_approve(args):
    """批量通过审核"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    ids = [int(x.strip()) for x in args.ids.split(',')]
    
    # 检查存在的记录数
    placeholders = ','.join('?' * len(ids))
    cursor.execute(f"SELECT COUNT(*) FROM check_ins WHERE id IN ({placeholders}) AND approved = 0", ids)
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(color("没有找到待审核的记录", Colors.YELLOW))
        conn.close()
        return
    
    if not args.force:
        confirm = input(f"确定要通过 {count} 条记录的审核吗? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            conn.close()
            return
    
    cursor.execute(f"""
        UPDATE check_ins 
        SET approved = 1, reviewed_at = ? 
        WHERE id IN ({placeholders}) AND approved = 0
    """, [datetime.now().isoformat()] + ids)
    conn.commit()
    
    print(color(f"✅ 已通过 {cursor.rowcount} 条记录的审核", Colors.GREEN))
    conn.close()


def cmd_review_stats(args):
    """显示审核统计"""
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM check_ins")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE approved = 1")
    approved = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM check_ins WHERE approved = 0")
    pending = cursor.fetchone()[0]
    
    print(color("\n📊 审核统计\n", Colors.HEADER))
    print(f"  总记录数:   {color(str(total), Colors.CYAN)}")
    print(f"  已通过:     {color(str(approved), Colors.GREEN)}")
    print(f"  待审核:     {color(str(pending), Colors.YELLOW)}")
    print()
    
    # 显示最近的待审核记录
    if pending > 0:
        cursor.execute("""
            SELECT id, nickname, content, review_reason, created_at 
            FROM check_ins 
            WHERE approved = 0
            ORDER BY id DESC 
            LIMIT 5
        """)
        rows = cursor.fetchall()
        print(color("最近待审核记录:\n", Colors.YELLOW))
        print_table(["ID", "昵称", "内容", "触发原因", "创建时间"], rows)
        print()
    
    conn.close()


# ============ 文件清理命令 ============

def cmd_orphan_files(args):
    """查找并清理孤儿文件（uploads中没有数据库引用的文件）"""
    import re
    
    uploads_dir = PROJECT_ROOT / "src" / "static" / "uploads"
    
    if not uploads_dir.exists():
        print(color("uploads 目录不存在", Colors.YELLOW))
        return
    
    conn = get_connection(args.db)
    cursor = conn.cursor()
    
    # 获取数据库中所有引用的文件路径
    cursor.execute("SELECT media_files FROM check_ins WHERE media_files != '[]'")
    rows = cursor.fetchall()
    
    referenced_files = set()
    for row in rows:
        try:
            media_list = json.loads(row[0])
            for media_url in media_list:
                # 从 URL 提取文件名: /static/uploads/2026-01/xxx.jpg -> 2026-01/xxx.jpg
                match = re.search(r'/uploads/(.+)$', media_url)
                if match:
                    referenced_files.add(match.group(1))
        except:
            pass
    
    conn.close()
    
    # 扫描 uploads 目录中的所有文件
    all_files = []
    total_size = 0
    
    for root, dirs, files in os.walk(uploads_dir):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(uploads_dir)
            file_size = file_path.stat().st_size
            all_files.append((str(rel_path), file_path, file_size))
            total_size += file_size
    
    # 找出孤儿文件
    orphan_files = []
    orphan_size = 0
    
    for rel_path, full_path, file_size in all_files:
        if rel_path not in referenced_files:
            orphan_files.append((rel_path, full_path, file_size))
            orphan_size += file_size
    
    # 显示统计
    print(color("\n📁 文件清理分析\n", Colors.HEADER))
    print(f"  {color('uploads 总文件数:', Colors.CYAN)} {len(all_files)}")
    print(f"  {color('uploads 总大小:', Colors.CYAN)} {format_size(total_size)}")
    print(f"  {color('数据库引用文件:', Colors.CYAN)} {len(referenced_files)}")
    print(f"  {color('孤儿文件数:', Colors.YELLOW)} {len(orphan_files)}")
    print(f"  {color('孤儿文件大小:', Colors.YELLOW)} {format_size(orphan_size)}")
    print()
    
    if not orphan_files:
        print(color("✅ 没有发现孤儿文件", Colors.GREEN))
        return
    
    # 显示孤儿文件列表
    if args.list or args.delete:
        print(color("孤儿文件列表:\n", Colors.YELLOW))
        for i, (rel_path, full_path, file_size) in enumerate(orphan_files[:50]):  # 最多显示50个
            print(f"  {i+1}. {rel_path} ({format_size(file_size)})")
        
        if len(orphan_files) > 50:
            print(f"  ... 还有 {len(orphan_files) - 50} 个文件")
        print()
    
    # 删除孤儿文件
    if args.delete:
        if not args.force:
            confirm = input(f"确定要删除 {len(orphan_files)} 个孤儿文件 ({format_size(orphan_size)}) 吗? (y/N): ")
            if confirm.lower() != 'y':
                print("已取消")
                return
        
        deleted_count = 0
        deleted_size = 0
        errors = []
        
        for rel_path, full_path, file_size in orphan_files:
            try:
                os.remove(full_path)
                deleted_count += 1
                deleted_size += file_size
            except Exception as e:
                errors.append(f"{rel_path}: {e}")
        
        # 清理空目录
        for root, dirs, files in os.walk(uploads_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):  # 目录为空
                        dir_path.rmdir()
                except:
                    pass
        
        print(color(f"✅ 已删除 {deleted_count} 个文件，释放 {format_size(deleted_size)}", Colors.GREEN))
        
        if errors:
            print(color(f"\n⚠️  {len(errors)} 个文件删除失败:", Colors.YELLOW))
            for err in errors[:5]:
                print(f"  - {err}")
    else:
        print(color("提示: 使用 --delete 参数删除这些文件", Colors.DIM))


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.2f} MB"
    else:
        return f"{size_bytes / 1024 / 1024 / 1024:.2f} GB"


def main():
    parser = argparse.ArgumentParser(
        description=color("📦 撸了吗 - 数据库运维管理工具", Colors.HEADER),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--db', default=str(DEFAULT_DB_PATH), 
                        help='数据库文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    p_list = subparsers.add_parser('list', help='列出所有记录')
    p_list.add_argument('--page', type=int, default=1, help='页码')
    p_list.add_argument('--size', type=int, default=10, help='每页数量')
    
    # show 命令
    p_show = subparsers.add_parser('show', help='查看单条记录详情')
    p_show.add_argument('id', type=int, help='记录ID')
    
    # delete 命令
    p_delete = subparsers.add_parser('delete', help='删除指定记录')
    p_delete.add_argument('id', type=int, help='记录ID')
    p_delete.add_argument('-f', '--force', action='store_true', help='跳过确认')
    
    # delete-range 命令
    p_delete_range = subparsers.add_parser('delete-range', help='删除ID范围内的记录')
    p_delete_range.add_argument('start', type=int, help='起始ID')
    p_delete_range.add_argument('end', type=int, help='结束ID')
    p_delete_range.add_argument('-f', '--force', action='store_true', help='跳过确认')
    
    # update 命令
    p_update = subparsers.add_parser('update', help='更新记录字段')
    p_update.add_argument('id', type=int, help='记录ID')
    p_update.add_argument('--content', help='内容')
    p_update.add_argument('--nickname', help='昵称')
    p_update.add_argument('--email', help='邮箱 (空字符串清除)')
    p_update.add_argument('--qq', help='QQ (空字符串清除)')
    p_update.add_argument('--url', help='链接 (空字符串清除)')
    p_update.add_argument('--avatar', help='头像emoji')
    p_update.add_argument('--love', type=int, help='点赞数')
    
    # search 命令
    p_search = subparsers.add_parser('search', help='搜索记录')
    p_search.add_argument('--content', help='内容关键词')
    p_search.add_argument('--nickname', help='昵称关键词')
    p_search.add_argument('--email', help='邮箱关键词')
    p_search.add_argument('--qq', help='QQ关键词')
    
    # stats 命令
    subparsers.add_parser('stats', help='显示数据库统计信息')
    
    # export 命令
    p_export = subparsers.add_parser('export', help='导出数据')
    p_export.add_argument('--format', choices=['json', 'csv'], default='json', help='导出格式')
    p_export.add_argument('--output', '-o', default='backup.json', help='输出文件名')
    
    # import 命令
    p_import = subparsers.add_parser('import', help='从JSON导入数据')
    p_import.add_argument('file', help='JSON文件路径')
    
    # vacuum 命令
    subparsers.add_parser('vacuum', help='压缩优化数据库')
    
    # clear 命令
    p_clear = subparsers.add_parser('clear', help='清空所有数据 (危险)')
    p_clear.add_argument('--confirm', action='store_true', help='确认执行')
    
    # sql 命令
    p_sql = subparsers.add_parser('sql', help='执行原始SQL')
    p_sql.add_argument('query', help='SQL语句')
    
    # ============ 审核管理命令 ============
    
    # pending 命令
    p_pending = subparsers.add_parser('pending', help='列出待审核记录')
    p_pending.add_argument('--page', type=int, default=1, help='页码')
    p_pending.add_argument('--size', type=int, default=10, help='每页数量')
    
    # approve 命令
    p_approve = subparsers.add_parser('approve', help='通过审核')
    p_approve.add_argument('id', type=int, help='记录ID')
    p_approve.add_argument('-f', '--force', action='store_true', help='跳过确认')
    
    # reject 命令
    p_reject = subparsers.add_parser('reject', help='拒绝并删除记录')
    p_reject.add_argument('id', type=int, help='记录ID')
    p_reject.add_argument('-f', '--force', action='store_true', help='跳过确认')
    
    # ban 命令
    p_ban = subparsers.add_parser('ban', help='拒绝并加入黑名单')
    p_ban.add_argument('id', type=int, help='记录ID')
    p_ban.add_argument('-f', '--force', action='store_true', help='跳过确认')
    
    # batch-approve 命令
    p_batch_approve = subparsers.add_parser('batch-approve', help='批量通过审核')
    p_batch_approve.add_argument('ids', help='记录ID列表，逗号分隔 (如: 1,2,3)')
    p_batch_approve.add_argument('-f', '--force', action='store_true', help='跳过确认')
    
    # review-stats 命令
    subparsers.add_parser('review-stats', help='显示审核统计')
    
    # ============ 文件清理命令 ============
    
    # orphan-files 命令
    p_orphan = subparsers.add_parser('orphan-files', help='查找/清理孤儿文件')
    p_orphan.add_argument('-l', '--list', action='store_true', help='列出孤儿文件')
    p_orphan.add_argument('-d', '--delete', action='store_true', help='删除孤儿文件')
    p_orphan.add_argument('-f', '--force', action='store_true', help='跳过确认')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应命令
    commands = {
        'list': cmd_list,
        'show': cmd_show,
        'delete': cmd_delete,
        'delete-range': cmd_delete_range,
        'update': cmd_update,
        'search': cmd_search,
        'stats': cmd_stats,
        'export': cmd_export,
        'import': cmd_import,
        'vacuum': cmd_vacuum,
        'clear': cmd_clear,
        'sql': cmd_sql,
        # 审核管理命令
        'pending': cmd_pending,
        'approve': cmd_approve,
        'reject': cmd_reject,
        'ban': cmd_ban,
        'batch-approve': cmd_batch_approve,
        'review-stats': cmd_review_stats,
        # 文件清理命令
        'orphan-files': cmd_orphan_files,
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()