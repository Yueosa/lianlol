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
    avatar TEXT DEFAULT '🥰',
    -- VERSION 3.0 新增字段
    love INTEGER DEFAULT 0
);
*/

-- ===================================
-- VERSION 4.0 - 压缩包支持
-- 创建时间: 2026-01-25
-- 说明: 添加压缩包上传支持，包含预览图提取和下载功能
-- 变更内容:
--   - 新增 file_type 字段，标识文件类型（'media' 或 'archive'），默认值 'media'
--   - 新增 archive_metadata 字段，存储压缩包元数据（JSON格式）
--   - 支持 ZIP 和 7Z 格式压缩包
--   - 文件大小限制从 20MB 提升到 50MB
--   - 自动提取压缩包中的预览图片（最多3张）
--   - 支持手动指定预览图片
-- archive_metadata JSON 结构:
--   {
--     "filename": "原始文件名.zip",
--     "size": 文件大小(字节),
--     "preview_images": ["预览图1路径", "预览图2路径", "预览图3路径"],
--     "total_files": 文件总数,
--     "image_count": 图片数量
--   }
-- ===================================

-- ===================================
-- VERSION 5.0 - 内容审核系统
-- 创建时间: 2026-01-25
-- 说明: 添加内容审核功能，支持智能检测和手动审核
-- 变更内容:
--   - 新增 approved 字段，审核状态（1=通过, 0=待审），默认值 1
--   - 新增 reviewed_at 字段，审核时间，可为 NULL
--   - 新增智能检测：字数过短/过长、黑名单关键词、无媒体文件
--   - 新增 /admin 管理后台，支持待审列表、通过、拒绝、批量操作
--   - 管理后台使用 ADMIN_KEY 环境变量进行鉴权
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
    love INTEGER DEFAULT 0,
    -- VERSION 4.0 新增字段
    file_type TEXT DEFAULT 'media',
    archive_metadata TEXT DEFAULT NULL,
    -- VERSION 5.0 新增字段
    approved INTEGER DEFAULT 1,
    reviewed_at DATETIME DEFAULT NULL
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
--
-- 从 V3.0 迁移到 V4.0:
-- ALTER TABLE check_ins ADD COLUMN file_type TEXT DEFAULT 'media';
-- ALTER TABLE check_ins ADD COLUMN archive_metadata TEXT DEFAULT NULL;
-- UPDATE check_ins SET file_type = 'media' WHERE file_type IS NULL;
--
-- 从 V4.0 迁移到 V5.0:
-- ALTER TABLE check_ins ADD COLUMN approved INTEGER DEFAULT 1;
-- ALTER TABLE check_ins ADD COLUMN reviewed_at DATETIME DEFAULT NULL;
-- UPDATE check_ins SET approved = 1 WHERE approved IS NULL;
-- ===================================
