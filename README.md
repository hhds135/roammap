# 城事绘图 (Urban Canvas)

一个基于 Web 的交互式地图应用，允许用户以"分享角落"的形式在地图上标记特殊地点。

## 项目特色

- 🗺️ **交互式地图展示**：全屏动态地图界面
- 📍 **用户分享功能**：标记地点，上传照片和故事
- 🔍 **社区发现体验**：探索他人分享的地点
- 🏷️ **标签筛选系统**：主题式地点探索
- 🔗 **链接分享机制**：每个角落都有唯一URL
- 👤 **基础用户系统**：简单的注册登录功能

## 技术栈

- **前端**：Vue 3 + Element Plus + Leaflet
- **后端**：Python Flask
- **数据存储**：JSON 文件（简化版本）
- **地图服务**：OpenStreetMap + Leaflet

## 项目结构

```
urban_canvas/
├── backend/           # Flask 后端 API
│   ├── app.py        # 主应用文件
│   ├── data/         # JSON 数据文件
│   └── uploads/      # 上传的图片
├── frontend/         # Vue 前端应用
└── README.md
```

## 快速开始

### 后端启动

```bash
cd backend
pip install flask flask-cors
python app.py
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 功能说明

### 核心功能

1. **交互式地图**：基于 Leaflet 的全屏地图界面
2. **角落分享**：用户可标记地点并分享照片、故事
3. **标签系统**：支持自定义标签和筛选功能
4. **社区探索**：浏览和发现其他用户分享的地点
5. **用户系统**：简单的注册、登录功能

### 数据存储

- `users.json`：用户账户信息
- `corners.json`：角落分享数据
- `uploads/`：用户上传的图片文件

## 开发说明

这是一个简化版本的实现，使用JSON文件存储数据，适合快速原型开发和演示。