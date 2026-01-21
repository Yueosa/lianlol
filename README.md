# 撸了吗 (lol)

一个基于 FastAPI + SQLite 的打卡系统，支持文本和多媒体（图片/视频）内容的提交与展示。

## 功能特性

- ✅ 文本打卡提交
- ✅ 多媒体文件上传（图片、视频，最大 20MB）
- ✅ 打卡记录展示
- ✅ URL 自动识别并渲染为链接
- ✅ 响应式设计
- ✅ 用户信息（昵称、头像、邮箱、QQ、链接）
- ✅ 高级搜索/筛选功能
- ✅ 数据库运维管理工具
- ✅ 测试数据生成工具

## 技术栈

- **后端**: Python FastAPI, SQLite3
- **前端**: HTML5, CSS3, 原生 JavaScript

## 安装 (推荐使用 `uv` 管理器)

```bash
uv sync
```

## 运行

```bash
uv run main.py
```

应用将在 http://localhost:8000 启动

## 页面访问

- 打卡提交页面: http://localhost:8000/
- 打卡展示页面: http://localhost:8000/display

## API 接口

- `POST /api/checkin` - 提交打卡
- `GET /api/checkins` - 获取打卡列表
- `POST /api/upload` - 上传文件
- `GET /static/*` - 访问静态文件

## 数据库工具

### 运维管理工具 (`scripts/db_admin.py`)

用于在服务器命令行环境对数据库进行运维、修改、更新。

```bash
# 列出记录
uv run scripts/db_admin.py list --page 1 --size 10

# 查看单条记录
uv run scripts/db_admin.py show 5

# 删除记录
uv run scripts/db_admin.py delete 5
uv run scripts/db_admin.py delete-range 1 10

# 更新记录
uv run scripts/db_admin.py update 5 --nickname "新昵称" --content "新内容"

# 搜索记录
uv run scripts/db_admin.py search --content "关键词" --nickname "用户"

# 数据库统计
uv run scripts/db_admin.py stats

# 导出/导入数据
uv run scripts/db_admin.py export --format json --output backup.json
uv run scripts/db_admin.py import backup.json

# 压缩优化数据库
uv run scripts/db_admin.py vacuum

# 清空所有数据 (危险)
uv run scripts/db_admin.py clear --confirm

# 执行原始SQL
uv run scripts/db_admin.py sql "SELECT * FROM checkins LIMIT 5"
```

### 测试数据生成工具 (`scripts/db_seed.py`)

用于快速生成大量测试数据，方便测试筛选/搜索功能。

```bash
# 插入50条随机数据
uv run scripts/db_seed.py --count 50

# 插入100条数据，时间分布在过去7天
uv run scripts/db_seed.py --count 100 --days 7

# 指定联系方式生成概率（50%）
uv run scripts/db_seed.py --count 50 --contact-rate 0.5

# 清空后重新生成
uv run scripts/db_seed.py --count 100 --clear-first
```

## 项目结构

```
lol/
├── main.py              # 入口文件
├── pyproject.toml       # 项目配置
├── README.md
├── data/                # 数据目录 (自动创建)
│   └── checkins.db      # SQLite 数据库
├── scripts/             # 工具脚本
│   ├── db_admin.py      # 数据库运维管理
│   └── db_seed.py       # 测试数据生成
├── src/
│   ├── api/             # API 路由
│   ├── db/              # 数据库模型
│   ├── utils/           # 工具函数
│   ├── html/            # HTML 模板
│   ├── css/             # 样式文件
│   ├── js/              # JavaScript
│   └── static/          # 静态资源
└── uploads/             # 上传文件目录 (自动创建)
```
