# 快速入门指南

## 1. 环境准备

### 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件
# 修改 .env 文件中的数据库和 Redis 配置
```

## 2. 测试配置

运行配置测试脚本：
```bash
python test_config.py
```

确保所有配置都正确无误。

## 3. 启动服务

### Windows 系统
```batch
# 安装依赖
start_celery.bat install

# 测试配置
start_celery.bat test

# 启动 Worker（新窗口）
start_celery.bat worker

# 启动 Beat（新窗口）
start_celery.bat beat

# 启动 Flower 监控（新窗口）
start_celery.bat flower
```

### Linux/Mac 系统
```bash
# 启动 Worker
celery -A demo_celery worker --loglevel=info --concurrency=4

# 启动 Beat（新终端）
celery -A demo_celery beat --loglevel=info

# 启动 Flower 监控（新终端）
celery -A demo_celery flower --port=5555
```

## 4. 创建任务表

在 MySQL 中创建任务队列表：

```sql
CREATE TABLE IF NOT EXISTS securities_update_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    security_code VARCHAR(10) NOT NULL COMMENT '证券代码',
    security_name VARCHAR(50) NOT NULL COMMENT '证券名称',
    update_type ENUM('price', 'volume', 'technical', 'all') DEFAULT 'all' COMMENT '更新类型',
    priority INT DEFAULT 0 COMMENT '优先级',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '状态',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='证券数据更新任务队列';
```

## 5. 添加测试数据

```sql
INSERT INTO securities_update_queue (security_code, security_name, update_type, priority) VALUES
('000001', '平安银行', 'all', 1),
('000002', '万科A', 'price', 2),
('000858', '五粮液', 'all', 1),
('002415', '海康威视', 'technical', 0),
('300059', '东方财富', 'all', 1);
```

## 6. 运行示例

```bash
python usage_example.py
```

## 7. 监控任务

访问 Flower 监控界面：
- 地址: http://localhost:5555
- 查看任务状态、队列长度、Worker 状态等

## 8. 常见问题

### Redis 连接失败
- 检查 Redis 服务是否启动
- 确认 `.env` 文件中的 Redis 配置正确

### 数据库连接失败
- 检查 MySQL 服务状态
- 确认 `.env` 文件中的数据库配置正确
- 确保数据库用户有足够的权限

### 任务执行失败
- 查看 Celery Worker 日志
- 检查 `update_security_data` 函数的实现
- 确认数据接口是否正常

### 内存使用过高
- 减少 Worker 并发数
- 调整 `worker_max_tasks_per_child` 参数

## 9. 自定义开发

在 `demo_celery.py` 的 `update_security_data` 函数中实现具体的数据更新逻辑：

```python
def update_security_data(security_code: str, update_type: str) -> bool:
    """
    具体的证券数据更新逻辑
    """
    try:
        if update_type == 'price':
            # 调用 tushare 或 akshare 获取价格数据
            # 更新到相应的数据表中
            pass
        elif update_type == 'volume':
            # 更新成交量数据
            pass
        elif update_type == 'technical':
            # 更新技术指标数据
            pass
        elif update_type == 'all':
            # 全部数据更新
            pass
        
        return True
    except Exception as e:
        logger.error(f"更新失败: {e}")
        return False
```

## 10. 生产部署

1. 使用 Supervisor 或 systemd 管理 Celery 进程
2. 配置 Nginx 反向代理 Flower 监控界面
3. 使用专业的 Redis 集群
4. 配置数据库连接池
5. 设置日志轮转和监控报警
