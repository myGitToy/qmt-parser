# Celery 证券数据更新系统

这是一个基于 Celery 的证券数据更新系统，用于批量处理 MySQL 数据库中的证券数据更新任务。

## 功能特点

- 支持单个证券数据更新
- 支持批量证券数据更新
- 任务状态跟踪和管理
- 错误处理和重试机制
- 分布式任务处理
- 监控和管理界面

## 环境要求

```bash
pip install celery[redis]
pip install mysql-connector-python
pip install flower  # 可选，用于监控界面
```

## 数据库准备

创建证券数据更新任务队列表：

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

## 配置设置

### 1. 环境变量配置

复制 `.env.example` 文件为 `.env`：

```bash
cp .env.example .env
```

然后根据您的实际环境修改 `.env` 文件中的配置：

```properties
# 数据库配置
DB_NAME=ubuntu186  # 选择要使用的数据库环境
UBUNTU186_DB_CONN=mysql+pymysql://root:q19840207@192.168.1.186:3306/stock

# Redis 配置
REDIS_HOST=192.168.1.201
REDIS_PORT=6379
REDIS_PASSWORD=

# 可选：Tushare API Token
TUSHARE_TOKEN=your_tushare_token_here
```

### 2. 支持的数据库环境

系统支持以下数据库环境，通过 `DB_NAME` 参数选择：

- `aliyun`: 阿里云数据库
- `aws`: AWS RDS 数据库
- `localhost`: 本地数据库
- `centos9`: CentOS 9 服务器
- `ubuntu186`: Ubuntu 186 服务器（默认）
- `ubuntu191`: Ubuntu 191 服务器
- `docker_201`: Docker 201 服务器

### 3. 配置验证

运行配置测试脚本验证配置是否正确：

```bash
python test_config.py
```

该脚本会测试：
- 环境变量加载
- 数据库连接
- Redis 连接
- Celery 配置

### 3. 配置说明

- `REDIS_HOST`: Redis 服务器地址
- `REDIS_PORT`: Redis 端口，默认 6379
- `REDIS_PASSWORD`: Redis 密码，如果没有设置密码则留空
- 系统会自动从环境变量中读取配置信息

## 使用方法

### 1. 启动 Redis 服务
```bash
redis-server
```

### 2. 启动 Celery Worker
```bash
python start_celery.py worker
```

### 3. 启动 Celery Beat（可选，用于定时任务）
```bash
python start_celery.py beat
```

### 4. 启动 Flower 监控界面（可选）
```bash
python start_celery.py flower
```

### 5. 一键启动所有服务
```bash
python start_celery.py all
```

## 代码示例

### 提交单个更新任务
```python
from usage_example import SecurityTaskManager

manager = SecurityTaskManager()
task_id = manager.submit_single_update('000001', '平安银行', 'price')
```

### 提交批量更新任务
```python
task_id = manager.submit_batch_update(batch_size=10)
```

### 检查任务状态
```python
status = manager.check_task_status(task_id)
print(status)
```

### 等待任务完成
```python
result = manager.wait_for_task(task_id, timeout=300)
if result and result['successful']:
    print(f"任务完成: {result['result']}")
```

## 任务类型

系统支持以下更新类型：

- `price`: 价格数据更新
- `volume`: 成交量数据更新
- `technical`: 技术指标更新
- `all`: 全部数据更新

## 监控和管理

### 使用 Flower 监控界面
访问 http://localhost:5555 查看：
- 任务执行状态
- 队列长度
- Worker 状态
- 任务历史记录

### 命令行管理
```bash
# 查看状态
python start_celery.py status

# 停止所有服务
python start_celery.py stop
```

## 扩展说明

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

## 注意事项

1. 确保 Redis 服务正在运行
2. 根据实际情况调整并发数和批次大小
3. 在生产环境中使用更安全的数据库连接配置
4. 考虑添加数据验证和清理机制
5. 定期清理已完成的任务记录

## 故障排除

### 常见问题

1. **连接 Redis 失败**
   - 检查 Redis 服务是否启动
   - 确认 Redis 连接配置正确

2. **数据库连接失败**
   - 检查 MySQL 服务状态
   - 确认数据库配置信息正确

3. **任务执行失败**
   - 查看日志文件 `celery_securities.log`
   - 检查数据接口是否正常

4. **内存使用过高**
   - 调整 `worker_max_tasks_per_child` 参数
   - 减少并发数

### 性能优化

1. 根据服务器资源调整 Worker 并发数
2. 使用合适的批次大小避免过载
3. 定期清理完成的任务记录
4. 考虑使用数据库连接池
