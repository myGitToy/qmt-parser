# QMT 数据校验模块架构文档

## 概述

QMT 数据校验模块用于扫描和浏览迅投 QMT 客户端本地缓存的数据文件，提供数据总览、市场目录浏览、文件列表查看等功能。

## 技术架构

### 数据流向

```
┌─────────────┐     HTTP      ┌─────────────┐     File I/O     ┌─────────────┐
│   前端      │ ──────────→  │   后端      │ ─────────────→  │ QMT datadir │
│  (React)    │              │ (FastAPI)   │                 │             │
└─────────────┘              └─────────────┘                 └─────────────┘
     │                            │                                 │
     │                            │                                 │
  qmt.ts                    qmt_service.py                    本地文件系统
  qmtStore.ts               QmtDataService
  QmtDataExplorer.tsx
```

### 组件说明

#### 1. 前端层

**API 客户端** (`src/api/qmt.ts`)
- 封装 HTTP 请求，与后端 API 通信
- 提供 `qmtApi` 对象，包含以下方法：
  - `getStatus()` - 获取 QMT 配置状态
  - `getSummary()` - 获取数据总览统计
  - `getMarkets()` - 获取市场列表
  - `getPeriods(market)` - 获取指定市场的周期列表
  - `getFiles(market, period, page, pageSize)` - 获取文件列表（分页）
  - `getFileInfo(path)` - 获取单个文件详细信息
  - `getOtherFiles()` - 获取其他文件（财务、分红等）

**状态管理** (`src/stores/qmtStore.ts`)
- 使用 Zustand 管理全局状态
- 存储数据：市场列表、周期列表、文件列表、分页信息
- 提供操作方法：数据获取、市场/周期选择、文件查看

**UI 组件** (`src/pages/qmt/QmtDataExplorer.tsx`)
- 主页面组件，展示数据校验界面
- 包含：统计卡片、市场目录树、文件列表表格
- 支持交互：刷新、目录选择、分页

#### 2. 后端层

**路由层** (`app/api/v1/qmt/__init__.py`)
- 定义 REST API 端点
- 路径前缀：`/api/v1/qmt`
- 依赖注入：`get_qmt_service()`

**服务层** (`app/services/qmt_service.py`)
- **核心类**：`QmtDataService`
- **数据来源**：QMT 客户端本地 `datadir` 目录
- **实现方式**：使用 Python `pathlib` 扫描文件系统

## 关键设计决策

### 1. 为什么不使用 qmt-parser？

**qmt-parser**（Rust 子模块）用于解析 QMT 数据文件的**二进制内容**，读取实际的股票数据记录（K线、Tick 等）。

而 QMT 数据校验模块只需要：
- 文件元信息（文件名、大小、修改时间）
- 目录结构浏览
- 文件数量统计

这些功能通过 Python 的 `Path.glob()` + `Path.stat()` 即可实现，无需解析文件内容，因此使用自有函数更加轻量高效。

**何时需要 qmt-parser：**
- 当需要读取文件内容（如 K线数据、Tick 数据）时
- 当需要验证数据完整性时
- 当需要数据转换或导出时

### 2. 类型导出方式

前端使用 TypeScript 的 `verbatimModuleSyntax` 模式，严格区分类型导入和值导入：

```typescript
// 正确 ✅
import { qmtApi } from "../api/qmt";           // 值导入
import type { FileInfo } from "../api/qmt";     // 类型导入

// 错误 ❌
import { qmtApi, FileInfo } from "../api/qmt";  // 混合导入
```

所有类型定义使用 `export type` 而非 `export interface`：

```typescript
// 正确 ✅
export type FileInfo = {
  name: string;
  path: string;
  // ...
};

// 错误 ❌
export interface FileInfo {
  name: string;
  path: string;
  // ...
}
```

### 3. 数据映射表

**市场代码映射** (MARKET_MAP)
```python
"SH" → 上海证券交易所 (沪, .SH)
"SZ" → 深圳证券交易所 (深, .SZ)
"BJ" → 北京证券交易所 (京, .BJ)
"SHO" → 上海期权
"SZO" → 深圳期权
```

**周期代码映射** (PERIOD_MAP)
```python
"0"     → Tick分笔 (tick)
"60"    → 1分钟 (1m)
"300"   → 5分钟 (5m)
"1800"  → 15分钟 (15m)
"3600"  → 1小时 (1h)
"86400" → 日线 (1d)
"43200" → 周线 (1w)
"1209600" → 月线 (1M)
```

## 文件结构

### Tick 数据结构
```
datadir/
├── SH/
│   └── 0/                          # Tick 目录
│       ├── 000001/                 # 股票代码
│       │   ├── 20250101.dat        # 日期文件
│       │   ├── 20250102.dat
│       │   └── ...
│       └── 600000/
│           └── ...
```

### K线数据结构
```
datadir/
├── SH/
│   ├── 60/                          # 1分钟
│   │   ├── 000001.SZ.DAT           # 股票文件
│   │   ├── 600000.SH.DAT
│   │   └── ...
│   ├── 300/                         # 5分钟
│   └── 86400/                       # 日线
└── SZ/
    └── ...
```

## API 端点

| 端点 | 方法 | 描述 | 返回 |
|------|------|------|------|
| `/api/v1/qmt/status` | GET | 获取 QMT 配置状态 | `{valid, error}` |
| `/api/v1/qmt/summary` | GET | 获取数据总览 | `{summary, markets}` |
| `/api/v1/qmt/markets` | GET | 列出所有市场 | `{markets, total}` |
| `/api/v1/qmt/markets/{market}/periods` | GET | 列出指定市场的周期 | `{market, periods, total}` |
| `/api/v1/qmt/markets/{market}/periods/{period}/files` | GET | 列出文件列表（分页） | `{files, pagination}` |
| `/api/v1/qmt/file-info?path=xxx` | GET | 获取单个文件详情 | `FileInfo` |
| `/api/v1/qmt/other-files` | GET | 获取其他文件信息 | `{files}` |

## 环境配置

### 后端环境变量 (`.env`)

```bash
# QMT 客户端路径
QMT_CLIENT_PATH=C:/path/to/qmt/client
```

### 前端环境变量

无需特殊配置，通过 Vite 代理访问后端：
```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8011',
    changeOrigin: true,
  },
}
```

## 性能优化

1. **文件统计优化**：使用 `glob` 模式匹配，避免遍历所有文件
2. **分页加载**：文件列表支持分页，默认每页 100 条
3. **懒加载**：周期列表按需加载，仅在选中市场后获取
4. **缓存策略**：可考虑对 `summary` 和 `markets` 进行缓存（未实现）

## 未来扩展

### 计划功能
- [ ] 文件内容预览（需要集成 qmt-parser）
- [ ] 数据完整性验证
- [ ] 数据导出功能（CSV/Parquet）
- [ ] 文件对比功能
- [ ] 数据备份管理

### 与 qmt-parser 集成

当需要读取文件内容时，可通过以下方式集成 qmt-parser：

```python
# 示例：读取 K线数据
from qmt_parser import KLineParser

parser = KLineParser()
data = parser.parse_file(file_path)
# data 包含：时间、开盘、最高、最低、收盘、成交量等
```

## 故障排查

### 常见问题

1. **QMT 未配置**
   - 错误：`QMT_CLIENT_PATH 未配置`
   - 解决：在后端 `.env` 中设置 `QMT_CLIENT_PATH`

2. **datadir 不存在**
   - 错误：`datadir 不存在: xxx/datadir`
   - 解决：确认 QMT 客户端已安装，路径正确

3. **文件列表为空**
   - 检查 QMT 客户端是否已下载行情数据
   - 确认选择的市场和周期有数据

## 维护者

- 模块位置：`apps/webui/securities-dashboard/`
- 后端服务：`backend/api/app/services/qmt_service.py`
- 前端页面：`frontend/client-web/src/pages/qmt/`
- 子模块：`libs/qmt-parser` (Rust)
