# CeleryHandler 消息队列演示

这个模块演示了如何使用 Celery 实现消息队列的基础操作。

## 文件说明

### 核心文件
- `celery_handler.py` - CeleryHandler 类，提供消息队列基础操作
- `celery_demo.py` - 使用演示脚本
- `start_celery.py` - Celery Worker 启动脚本

### 功能特性

#### CeleryHandler 类提供的功能：
1. **简单任务** - 基础的异步任务执行
2. **长时间任务** - 支持进度更新的长时间运行任务
3. **批量任务** - 批量处理数据，支持进度跟踪
4. **错误处理** - 自动重试机制演示
5. **任务管理** - 任务状态查询、取消、等待完成
6. **队列监控** - 队列信息查看、统计

## 快速开始

### 1. 环境准备

确保已安装依赖：
```bash
pip install celery redis pandas
```

确保 Redis 服务正在运行：
```bash
# Windows (如果使用 WSL 或 Docker)
redis-server

# 或者使用 Docker
docker run -d -p 6379:6379 redis:latest
```

### 2. 启动 Celery Worker

```bash
# 方法1：使用启动脚本
python start_celery.py worker

# 方法2：直接使用 celery 命令
celery -A celery_handler:CeleryHandler.app worker --loglevel=info
```

### 3. 运行演示

在另一个终端中运行演示脚本：
```bash
python celery_demo.py
```

## 基础操作示例

### 提交简单任务
```python
from celery_handler import CeleryHandler

handler = CeleryHandler()

# 提交任务
task_id = handler.submit_simple_task("Hello World!", delay=2)
print(f"任务ID: {task_id}")

# 等待结果
result = handler.wait_for_task(task_id, timeout=10)
print(f"结果: {result}")
```

### 批量处理任务
```python
# 准备数据
items = [f"数据_{i}" for i in range(1, 21)]

# 提交批量任务
task_id = handler.submit_batch_task(items, batch_size=5)

# 监控进度
while True:
    status = handler.get_task_status(task_id)
    if status.get('state') == 'PROGRESS':
        progress = status.get('progress', {})
        print(f"进度: {progress.get('percentage', 0)}%")
    elif status.get('ready'):
        print("任务完成!")
        break
    time.sleep(1)
```

### 长时间任务
```python
# 提交长时间任务
task_id = handler.submit_long_task(duration=30, progress_updates=True)

# 监控进度
while True:
    status = handler.get_task_status(task_id)
    if status.get('state') == 'PROGRESS':
        progress = status.get('progress', {})
        print(f"进度: {progress.get('message', '进行中...')}")
    elif status.get('ready'):
        break
    time.sleep(2)
```

### 任务管理
```python
# 查看任务状态
status = handler.get_task_status(task_id)
print(f"状态: {status}")

# 取消任务
cancel_result = handler.cancel_task(task_id)
print(f"取消结果: {cancel_result}")

# 查看队列信息
queue_info = handler.get_queue_info()
print(f"队列信息: {queue_info}")
```

## 任务类型

### 1. 简单任务 (simple_task)
- 队列: `default`
- 功能: 执行简单的延迟任务
- 参数: `message` (消息), `delay` (延迟秒数)

### 2. 长时间任务 (long_running_task)
- 队列: `long_tasks`
- 功能: 长时间运行，支持进度更新
- 参数: `duration` (持续时间), `progress_updates` (是否更新进度)

### 3. 批量任务 (batch_task)
- 队列: `batch`
- 功能: 批量处理数据项
- 参数: `items` (数据列表), `batch_size` (批次大小)

### 4. 错误任务 (error_task)
- 队列: `default`
- 功能: 演示错误处理和重试机制
- 参数: `should_fail` (是否失败), `error_message` (错误消息)

## 监控和管理

### 查看 Worker 状态
```bash
python start_celery.py status
```

### 监控任务执行
```bash
# 查看活动任务
celery -A celery_handler:CeleryHandler.app inspect active

# 查看统计信息
celery -A celery_handler:CeleryHandler.app inspect stats
```

### 清空队列
```python
# 清空所有队列
result = handler.purge_queue()
print(f"清空结果: {result}")
```

## 配置说明

### Redis 配置
默认配置在 `config.py` 中：
```python
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'broker_db': 1,    # 消息代理数据库
    'result_db': 2,    # 结果存储数据库
}
```

### Celery 配置
- **消息代理**: Redis
- **结果后端**: Redis
- **序列化**: JSON
- **时区**: Asia/Shanghai
- **任务确认**: Late ACK
- **结果过期**: 1小时

## 故障排除

### 常见问题

1. **Redis 连接失败**
   ```
   确保 Redis 服务正在运行
   检查 Redis 连接配置
   ```

2. **任务不执行**
   ```
   确保 Celery Worker 正在运行
   检查队列名称是否正确
   查看 Worker 日志
   ```

3. **导入错误**
   ```
   确保所有依赖已安装
   检查 Python 路径配置
   ```

### 调试模式

启用详细日志：
```bash
celery -A celery_handler:CeleryHandler.app worker --loglevel=debug
```

## 扩展和定制

### 添加自定义任务
```python
@handler.app.task(name='custom.my_task', bind=True)
def my_custom_task(self, param1, param2):
    # 自定义任务逻辑
    return {'result': 'success'}
```

### 自定义队列
```python
# 在配置中添加新队列
task_routes = {
    'custom.my_task': {'queue': 'custom_queue'},
}
```

### 钩子函数
```python
@handler.app.task(bind=True)
def task_with_hooks(self):
    # 任务开始钩子
    self.update_state(state='STARTED', meta={'message': '任务开始'})
    
    # 任务逻辑
    # ...
    
    # 任务完成钩子
    return {'status': 'completed'}
```

## 性能优化

1. **Worker 并发数**: 根据 CPU 核心数调整
2. **预取乘数**: 设置为 1 以避免任务堆积
3. **任务确认**: 使用 Late ACK 保证任务不丢失
4. **结果过期**: 及时清理过期结果
5. **队列分离**: 不同类型任务使用不同队列

## 生产环境部署

### 1. 使用进程管理器
```bash
# 使用 supervisor 或 systemd 管理 Worker 进程
```

### 2. 监控和告警
```bash
# 集成 Prometheus、Grafana 等监控工具
```

### 3. 高可用配置
```bash
# Redis 集群或主从配置
# 多个 Worker 节点
```

这个 CeleryHandler 演示了消息队列的基本使用模式，可以作为构建更复杂分布式系统的基础。
