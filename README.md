# 撸了吗 (lol)

一个基于 FastAPI + SQLite 的打卡系统，支持文本和多媒体（图片/视频）内容的提交与展示。

## 功能特性

- ✅ 文本打卡提交
- ✅ 多媒体文件上传（图片、视频，最大 20MB）
- ✅ 打卡记录展示
- ✅ URL 自动识别并渲染为链接
- ✅ 响应式设计

## 技术栈

- **后端**: Python FastAPI, SQLite3
- **前端**: HTML5, CSS3, 原生 JavaScript

## 安装

```bash
pip install -e .
```

## 运行

```bash
python main.py
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
