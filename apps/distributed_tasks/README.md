# 分布式股票数据处理系统

基于Redis和Celery的分布式股票数据更新系统，完全模仿akshare的`update_sequence_add`和`update_sequence_launch`功能。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Task Producer │    │   Redis Queue   │    │  Task Consumer  │
│  (生产者)        │───▶│   (任务队列)     │───▶│   (消费者)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │  Celery Tasks   │              │
         │              │  (分布式任务)    │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        MySQL Database                          │
│                        (最终数据存储)                           │
└─────────────────────────────────────────────────────────────────┘
```

## 核心功能

### 1. Redis数据结构管理 (`redis_manager.py`)
- 任务队列管理（按优先级分类）
- 任务状态跟踪
- 数据缓存
- 健康检查和统计

### 2. Celery分布式任务 (`celery_tasks.py`)
- 股票数据处理任务
- ETF数据处理任务
- 数据库存储任务
- 定时清理任务

### 3. 任务生产者 (`task_producer.py`)
- 模仿`update_sequence_add`功能
- 批量任务创建
- 证券代码自动获取
- 标准序列模板

### 4. 任务消费者 (`task_consumer.py`)
- 模仿`update_sequence_launch`功能
- 支持Celery和直接处理两种模式
- 任务统计和监控
- 优雅停止机制

### 5. 数据库连接器 (`mysql_connector.py`)
- MySQL连接管理
- 数据差值计算和存储
- 表结构管理
- 备份和恢复

### 6. 统一管理器 (`task_manager.py`)
- 整合所有组件
- 完整工作流程管理
- 系统状态监控
- 紧急停止功能

## 安装和配置

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 环境配置
创建`.env`文件：
```bash
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=myfunds
MYSQL_CHARSET=utf8mb4

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_WORKER_CONCURRENCY=4

# 任务配置
TASK_SLEEP_INTERVAL=0.05
TASK_MAX_RETRIES=3
DATA_RETENTION_HOURS=24

# 环境设置
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. 启动服务

#### 启动Redis服务器
```bash
redis-server
```

#### 启动Celery Worker
```bash
celery -A distributed_tasks.celery_tasks worker --loglevel=info --concurrency=4
```

#### 启动Celery Beat调度器（可选）
```bash
celery -A distributed_tasks.celery_tasks beat --loglevel=info
```

#### 启动Flower监控（可选）
```bash
celery -A distributed_tasks.celery_tasks flower
```

## 使用示例

### 基本使用

```python
from distributed_tasks.task_manager import DistributedTaskManager
from datetime import datetime, timedelta

# 创建管理器
manager = DistributedTaskManager()

# 添加更新序列（模仿akshare.update_sequence_add）
result = manager.update_sequence_add(
    code_list=['000001', '000002', '600000'],
    myclass='stock',
    ktype='1m',
    priority=1,
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)

# 启动序列更新（模仿akshare.update_sequence_launch）
launch_result = manager.update_sequence_launch(
    priority=1,
    sleep=0.05,
    use_celery=True
)
```

### 完整工作流程

```python
# 运行完整的更新周期
cycle_result = manager.run_complete_update_cycle(
    start_date=datetime(2024, 6, 20),
    end_date=datetime.now()
)

# 获取系统状态
status = manager.get_comprehensive_status()
print(f"系统状态: {status['system_status']}")
```

### 模仿原始akshare工作流

```python
# 模拟原始工作流程
akshare_result = manager.simulate_akshare_workflow()
```

## 数据结构对比

### akshare原始结构
```python
# 原始akshare使用方式
a = data()
a.start_date = datetime(2024, 6, 20)
a.end_date = datetime.now()
a.update_sequence_add(myclass='stock', type='1m', priority=1)
a.update_sequence_launch(priority=1, sleep=0.05)
```

### 分布式系统对应结构
```python
# 分布式系统对应使用方式
manager = DistributedTaskManager()
manager.update_sequence_add(
    myclass='stock', 
    ktype='1m', 
    priority=1,
    start_date=datetime(2024, 6, 20),
    end_date=datetime.now()
)
manager.update_sequence_launch(priority=1, sleep=0.05)
```

## 监控和管理

### 1. 系统状态监控
```python
# 获取综合状态
status = manager.get_comprehensive_status()

# Redis统计
redis_stats = status['redis']['statistics']

# MySQL表信息
mysql_tables = status['mysql']['table_info']

# 消费者统计
consumer_stats = status['consumer']
```

### 2. 清理和维护
```python
# 清理系统
cleanup_result = manager.cleanup_system()

# 紧急停止
emergency_result = manager.emergency_stop()
```

### 3. Flower Web界面
访问 `http://localhost:5555` 查看Celery任务监控界面。

## 优势特性

### 1. 高可用性
- Redis持久化保证任务不丢失
- 支持主从和集群模式
- 优雅的错误处理和重试机制

### 2. 水平扩展
- 支持多个Worker节点
- 任务自动负载均衡
- 按优先级处理任务

### 3. 监控和运维
- 实时任务状态跟踪
- 详细的统计信息
- Web界面监控

### 4. 数据安全
- 差值更新避免重复数据
- 自动备份功能
- 事务保证数据一致性

### 5. 配置灵活
- 支持多环境配置
- 热配置更新
- 详细的配置验证

## 性能优化

### 1. Redis优化
- 使用管道批量操作
- 合理设置过期时间
- 监控内存使用

### 2. MySQL优化
- 批量插入数据
- 合理的索引设计
- 连接池管理

### 3. Celery优化
- 合理设置并发数
- 使用消息确认机制
- 任务结果及时清理

## 故障排除

### 常见问题

1. **Redis连接失败**
   - 检查Redis服务是否启动
   - 验证连接配置
   - 检查防火墙设置

2. **MySQL连接失败** 
   - 确认数据库服务运行
   - 验证用户权限
   - 检查字符集设置

3. **Celery任务不执行**
   - 确认Worker进程运行
   - 检查队列名称配置
   - 验证任务路由设置

4. **数据重复或丢失**
   - 检查差值计算逻辑
   - 验证唯一键约束
   - 监控事务处理

### 日志分析
系统产生详细的日志信息，可以通过日志分析排查问题：

```bash
# 查看系统日志
tail -f logs/distributed_tasks.log

# 过滤错误日志
grep "ERROR" logs/distributed_tasks.log

# 查看特定任务日志
grep "task_id_xxx" logs/distributed_tasks.log
```

## 扩展开发

### 添加新的数据源
```python
# 在celery_tasks.py中添加新的处理函数
@app.task(name='process_new_data_source')
def process_new_data_source(task_data):
    # 实现新数据源的处理逻辑
    pass
```

### 自定义任务类型
```python
# 扩展任务生产者
class CustomTaskProducer(TaskProducer):
    def add_custom_sequence(self, custom_params):
        # 实现自定义序列逻辑
        pass
```

### 集成其他存储后端
```python
# 实现新的存储连接器
class PostgreSQLConnector:
    # 实现PostgreSQL存储逻辑
    pass
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。
