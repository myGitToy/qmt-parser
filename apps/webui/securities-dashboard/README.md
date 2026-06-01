# 证券看板平台

类似彭博终端或同花顺的专业证券看板平台，采用前后端分离架构。

## 技术栈

### 前端
- React 18 + TypeScript
- Vite
- Ant Design 5.x
- Zustand（状态管理）
- TradingView Lightweight Charts（K线图）
- AG Grid（数据表格）
- Socket.IO Client（实时通信）

### 后端
- FastAPI
- Python 3.11+
- PostgreSQL + TimescaleDB（时序数据）
- Redis（缓存）
- Tushare Pro（主数据源）
- AKShare（备用数据源）

## 项目结构

```
securities-dashboard/
├── frontend/
│   └── client-web/          # React 前端
│       ├── src/
│       │   ├── api/         # API 客户端
│       │   ├── components/  # 组件
│       │   ├── pages/       # 页面
│       │   ├── stores/      # 状态管理
│       │   ├── theme/       # 主题配置
│       │   └── types/       # 类型定义
│       └── package.json
│
├── backend/
│   └── api/                 # FastAPI 后端
│       ├── app/
│       │   ├── api/         # 路由
│       │   ├── core/        # 配置
│       │   ├── models/      # 数据模型
│       │   ├── providers/   # 数据源提供者
│       │   └── services/    # 业务逻辑
│       └── requirements.txt
│
├── shared/
│   └── types/               # 共享类型定义
│
├── docker/
│   ├── nginx/
│   │   └── nginx.conf
│   └── docker-compose.yml
│
└── README.md
```

## 快速开始

### 1. 安装依赖

**后端：**
```bash
cd backend/api
pip install -r requirements.txt
```

**前端：**
```bash
cd frontend/client-web
npm install
```

### 2. 配置环境变量

复制后端 `.env.example` 到 `.env` 并配置：
```bash
cp backend/api/.env.example backend/api/.env
```

编辑 `.env` 文件，设置 Tushare Token：
```
TUSHARE_TOKEN=your_token_here
```

### 3. 启动服务

**启动后端：**
```bash
cd backend/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端：**
```bash
cd frontend/client-web
npm run dev
```

### 4. 访问应用

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### Docker 部署

```bash
cd docker
docker-compose up -d
```

访问：http://localhost:8080

## 功能

### 已实现
- ✅ 市场概览（主要指数）
- ✅ K线图表（TradingView Lightweight Charts）
- ✅ 实时行情报价
- ✅ 自选股列表
- ✅ 暗色主题

### 规划中
- ⏳ 组合管理
- ⏳ 技术分析指标
- ⏳ 实时数据推送（WebSocket）
- ⏳ 回测平台（Backtrader）
- ⏳ 策略开发

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| F2 | 搜索股票 |
| F6 | 切换K线周期 |
| Esc | 返回上一级 |

## 架构模式

项目采用以下设计模式：

1. **提供者模式**：数据源抽象（Tushare/AKShare）
2. **仓储模式**：数据访问层分离
3. **服务层模式**：业务逻辑封装
4. **状态管理**：Zustand 全局状态

## UI 设计

- **布局**：三栏式（功能树 + 主工作区 + 信息栏）
- **主题**：暗色主题（参考彭博终端）
- **色彩**：红涨绿跌（A股习惯）

## 许可证

MIT

## 联系方式

- 作者：Hui Qiao
- 项目位置：`MyFunds/apps/webui/securities-dashboard/`
