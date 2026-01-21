-- ===================================
-- 数据库架构版本历史
-- ===================================
-- 此文件记录每个版本的完整数据库架构
-- 便于追踪变更和未来的数据库迁移
-- ===================================

-- ===================================
-- VERSION 1.0 - 初始版本
-- 创建时间: 2026-01-20
-- 说明: 基础的打卡记录系统
-- ===================================
/*
CREATE TABLE check_ins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    media_files TEXT DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT
);
*/

-- ===================================
-- VERSION 2.0 - 用户信息扩展
-- 创建时间: 2026-01-22
-- 说明: 添加用户信息字段（昵称、邮箱、QQ、URL、头像）
-- 变更内容:
--   - 新增 nickname 字段，默认值 '用户0721'
--   - 新增 email 字段，可选
--   - 新增 qq 字段，可选
--   - 新增 url 字段，可选
--   - 新增 avatar 字段，存储 emoji，默认值 '🥰'
-- ===================================
/*
CREATE TABLE IF NOT EXISTS check_ins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    media_files TEXT DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    -- VERSION 2.0 新增字段
    nickname TEXT DEFAULT '用户0721',
    email TEXT,
    qq TEXT,
    url TEXT,
    avatar TEXT DEFAULT '🥰'
);
*/

-- ===================================
-- VERSION 3.0 - 点赞功能
-- 创建时间: 2026-01-22
-- 说明: 添加点赞功能，支持按点赞数排序
-- 变更内容:
--   - 新增 love 字段，记录点赞数，默认值 0
--   - 新增 likes 表，记录点赞关系（IP + 记录ID），防止刷赞
-- ===================================

CREATE TABLE IF NOT EXISTS check_ins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    media_files TEXT DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    -- VERSION 2.0 新增字段
    nickname TEXT DEFAULT '用户0721',
    email TEXT,
    qq TEXT,
    url TEXT,
    avatar TEXT DEFAULT '🥰',
    -- VERSION 3.0 新增字段
    love INTEGER DEFAULT 0
);

-- 点赞记录表（防止重复点赞）
CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkin_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(checkin_id, ip_address),
    FOREIGN KEY (checkin_id) REFERENCES check_ins(id) ON DELETE CASCADE
);

-- 为点赞查询创建索引
CREATE INDEX IF NOT EXISTS idx_likes_checkin_ip ON likes(checkin_id, ip_address);

-- ===================================
-- 迁移说明
-- ===================================
-- 从 V1.0 迁移到 V2.0:
-- ALTER TABLE check_ins ADD COLUMN nickname TEXT DEFAULT '用户0721';
-- ALTER TABLE check_ins ADD COLUMN email TEXT;
-- ALTER TABLE check_ins ADD COLUMN qq TEXT;
-- ALTER TABLE check_ins ADD COLUMN url TEXT;
-- ALTER TABLE check_ins ADD COLUMN avatar TEXT DEFAULT '🥰';
--
-- 从 V2.0 迁移到 V3.0:
-- ALTER TABLE check_ins ADD COLUMN love INTEGER DEFAULT 0;
-- CREATE TABLE likes (...);
-- CREATE INDEX idx_likes_checkin_ip ON likes(checkin_id, ip_address);
-- ===================================
