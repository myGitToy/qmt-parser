# 证券看板启动指南

## 问题诊断

- **前端状态**: ✅ 已完整开发
  - Dashboard页面（K线图、行情表格、自选股）
  - MainLayout布局（左侧菜单、中间工作区、右侧资讯）
  - 路由和状态管理

- **后端状态**: ❌ 环境配置问题
  - API路由返回404
  - 需要使用 conda_myfund Python环境

## 解决步骤

### 1. 检查Python环境
```bash
# 激活conda环境
conda activate conda_myfund

# 验证依赖
python -c "import fastapi; print('FastAPI版本:', fastapi.__version__)"
```

### 2. 启动服务

**方法1：使用一键启动脚本（推荐）**
```bash
cd apps/webui
python start_webui.py
```

**方法2：分别启动**
```bash
# 终端1：启动后端
cd apps/webui/securities-dashboard/backend/api
conda activate conda_myfund
python -m uvicorn main:app --host 0.0.0.0 --port 8011 --reload

# 终端2：启动前端
cd apps/webui/securities-dashboard/frontend/client-web
npm run dev
```

### 3. 验证服务

- **前端**: http://localhost:5073
- **后端API文档**: http://localhost:8011/docs
- **健康检查**: http://localhost:8011/health
- **市场概览API**: http://localhost:8011/api/v1/market/overview

## 常见问题

**Q: 5073端口空白，没有内容？**
- 检查后端是否正常启动
- 打开浏览器控制台查看是否有API请求错误
- 确认使用了正确的Python环境

**Q: API返回404？**
- 确认后端使用conda_myfund环境
- 检查.env文件中tushare_token是否配置
- 查看后端启动日志

**Q: 前端JS加载失败？**
- 检查node_modules是否存在
- 运行 `npm install` 重新安装依赖
- 清除浏览器缓存重试

## 下一步

启动成功后，你应该看到：
1. 证券看板标题栏和功能菜单
2. 市场指数概览卡片
3. K线图表区域
4. 自选股和市场行情表格