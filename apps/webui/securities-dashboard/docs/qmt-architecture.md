# QMT 数据校验模块架构文档

## 概述

QMT 数据校验模块用于扫描和浏览迅投 QMT 客户端本地缓存的数据文件，支持 **5种数据类型** 的浏览和校验：

| 数据类型 | 目录树结构 | 后端路径 |
|----------|-----------|---------|
| **K线数据**   | 市场 → 周期 → 文件         | `datadir/{market}/{period}/`                      |
| **财务数据** | 报表类型 → 市场 → 文件     | `datadir/{market}/` + `finance/`                 |
| **除权数据** | 市场 → 文件                | `DividData/` (LevelDB)                            |
| **分笔成交** | 市场 → 股票代码 → 日期文件 | `datadir/{market}/0/{stock}/`                     |
| **ETF申赎**  | 市场 → ETF代码 → 文件      | `datadir/{market}/etf/` 或日线K线中ETF代码        |

## UI设计

采用**金融终端风格**布局（参考彭博终端/同花顺）：

- **功能区切换**: `<Segmented>` 胶囊式控件，在5种数据类型间切换
- **主从面板**: 左侧6/24目录导航 + 右侧18/24数据表格
- **底部状态栏**: 显示当前选择路径和最后更新时间
- **紧凑样式**: 11-12px字号、8px间距、暗色主题(`#0d1117`)

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
  - `getFiles(market, period, page, pageSize)` - 获取K线文件列表（分页）
  - `getFileInfo(path)` - 获取单个文件详细信息
  - `getOtherFiles()` - 获取其他文件（财务、分红等）
  - `getFinanceTypes()` - 获取财务数据类型列表
  - `getFinanceFiles(financeType, market, page, pageSize)` - 获取财务文件列表
  - `getTickStocks(market)` - 获取分笔成交股票代码列表
  - `getEtfCodes(market)` - 获取ETF代码列表
  - `getEtfFiles(market, code, page, pageSize)` - 获取ETF申赎文件列表
  - `getDividendFiles(market, page, pageSize)` - 获取除权文件列表

**状态管理** (`src/stores/qmtStore.ts`)
- 使用 Zustand 管理全局状态
- 存储数据：市场列表、周期列表、财务类型、Tick股票列表、ETF列表、文件列表、分页信息
- 核心状态：`activeDataType` 控制当前展示的数据类型（kline/finance/dividend/tick/etf）
- 提供操作方法：数据类别切换、各类型数据获取、选择、文件查看

**UI 组件** (`src/pages/qmt/QmtDataExplorer.tsx`)
- 主页面组件，采用金融终端风格布局
- 功能区切换：`<Segmented>` 胶囊式控件，5种数据类型
- 主从面板：左侧目录导航（6/24）+ 右侧数据表格（18/24）
- 配置驱动：通过 `Record<DataType, ...>` 映射不同的目录树结构和表格列定义
- 底部状态栏：显示当前选择路径和最后更新时间

#### 2. 后端层

**路由层** (`app/api/v1/qmt/__init__.py`)
- 定义 REST API 端点
- 路径前缀：`/api/v1/qmt`
- 依赖注入：`get_qmt_service()`

**服务层** (`app/services/qmt_service.py`)
- **核心类**：`QmtDataService`
- **数据来源**：QMT 客户端本地 `datadir` 目录及相邻目录（`finance/`、`DividData/`）
- **实现方式**：使用 Python `pathlib` 扫描文件系统
- **输入验证**：所有 API 端点对 `market`、`finance_type` 参数进行白名单校验

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
// 正确
import { qmtApi } from "../api/qmt";           // 值导入
import type { FileInfo } from "../api/qmt";     // 类型导入

// 错误
import { qmtApi, FileInfo } from "../api/qmt";  // 混合导入
```

所有类型定义使用 `export type` 而非 `export interface`。

### 3. 核心类型定义

```typescript
// 数据类别（控制UI功能区切换）
type DataType = "kline" | "finance" | "dividend" | "tick" | "etf";

// 通用分页响应
type PaginatedResponse<T> = {
    valid: boolean;
    files: T[];
    pagination: { page: number; page_size: number; total: number; total_pages: number };
};

// 各数据类型的专用类型
type FinanceTypeInfo = { code: string; name: string; files: number; ... };
type TickStockInfo   = { code: string; market: string; files: number; ... };
type EtfInfo         = { code: string; market: string; source: string; ... };
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

**财务数据类型映射** (FINANCE_TYPE_MAP)
```python
"7001" → 资产负债表 (_7001.DAT)
"7002" → 利润表 (_7002.DAT)
"7003" → 现金流量表 (_7003.DAT)
"7004" → 杜邦分析 (_7004.DAT)
"7005" → 盈利能力 (_7005.DAT)
"7006" → 成长能力 (_7006.DAT)
"7007" → 偿债能力 (_7007.DAT)
"7008" → 营运能力 (_7008.DAT)
```

**ETF代码前缀映射**
```python
"SH" → ["51", "56", "58", "59", "50"]  # 上交所ETF
"SZ" → ["15", "16"]                      # 深交所ETF
```

## 文件结构

### K线数据结构
```
datadir/
├── SH/
│   ├── 60/                          # 1分钟
│   │   ├── 000001.SZ.DAT           # 股票文件
│   │   ├── 600000.SH.DAT
│   │   └── ...
│   ├── 300/                         # 5分钟
│   ├── 86400/                       # 日线
│   └── 0/                           # Tick分笔（见下方）
└── SZ/
    └── ...
```

### Tick数据结构
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

### 财务数据结构
```
datadir/../                          # QMT客户端根目录
├── datadir/
│   ├── SH/
│   │   ├── *_7001.DAT              # 资产负债表
│   │   ├── *_7002.DAT              # 利润表
│   │   └── ...
│   └── SZ/
│       └── ...
└── finance/                         # 独立财务数据目录
    ├── *_7001.DAT
    └── ...
```

### 除权数据结构
```
datadir/../                          # QMT客户端根目录
└── DividData/                       # LevelDB 数据库
    ├── *.ldb
    ├── *.log
    └── MANIFEST-*
```

### ETF申赎数据结构

ETF数据可能存在于以下路径（自动探测）：

- `datadir/{market}/etf/` 或 `datadir/{market}/ETF/` — 专用ETF目录
- `datadir/{market}/86400/` — 从日线K线中按代码前缀识别（SH: 51/56/58/59/50, SZ: 15/16）

## API 端点

### 基础端点

| 端点 | 方法 | 描述 | 返回 |
|------|------|------|------|
| `/api/v1/qmt/status` | GET | 获取 QMT 配置状态 | `{valid, error}` |
| `/api/v1/qmt/summary` | GET | 获取数据总览 | `{summary, markets}` |
| `/api/v1/qmt/markets` | GET | 列出所有市场 | `{markets, total}` |
| `/api/v1/qmt/markets/{market}/periods` | GET | 列出指定市场的周期 | `{market, periods, total}` |
| `/api/v1/qmt/markets/{market}/periods/{period}/files` | GET | 列出K线文件列表（分页） | `{files, pagination}` |
| `/api/v1/qmt/file-info?path=xxx` | GET | 获取单个文件详情 | `FileInfo` |
| `/api/v1/qmt/other-files` | GET | 获取其他文件信息 | `{files}` |

### 财务数据端点

| 端点 | 方法 | 描述 | 参数验证 |
|------|------|------|---------|
| `/api/v1/qmt/finance/types` | GET | 列出财务数据类型 | - |
| `/api/v1/qmt/finance/{finance_type}/markets/{market}/files` | GET | 列出财务文件（分页） | `finance_type` ∈ 7001-7008, `market` ∈ SH/SZ/BJ/SZO/SHO |

### 分笔成交端点

| 端点 | 方法 | 描述 | 参数验证 |
|------|------|------|---------|
| `/api/v1/qmt/tick/markets/{market}/stocks` | GET | 列出有Tick数据的股票 | `market` ∈ SH/SZ/BJ/SZO/SHO |

### ETF申赎端点

| 端点 | 方法 | 描述 | 参数验证 |
|------|------|------|---------|
| `/api/v1/qmt/etf/markets/{market}/codes` | GET | 列出ETF代码 | `market` ∈ SH/SZ/BJ/SZO/SHO |
| `/api/v1/qmt/etf/markets/{market}/codes/{code}/files` | GET | 列出ETF文件（分页） | `market` ∈ SH/SZ/BJ/SZO/SHO |

### 除权数据端点

| 端点 | 方法 | 描述 | 参数验证 |
|------|------|------|---------|
| `/api/v1/qmt/dividend/markets/{market}/files` | GET | 列出除权文件（分页） | `market` ∈ SH/SZ/BJ/SZO/SHO |

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
