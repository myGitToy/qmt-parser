"""
使用示例和管理脚本
"""

import time
from demo_celery import (
    app, 
    submit_batch_update, 
    check_task_result,
    update_single_security,
    batch_update_securities,
    get_task_status
)


class SecurityTaskManager:
    """证券任务管理器"""
    
    def __init__(self):
        self.app = app
    
    def submit_single_update(self, security_code, security_name, update_type='all'):
        """提交单个证券更新任务"""
        security_info = {
            'id': int(time.time()),  # 临时ID，实际使用时从数据库获取
            'security_code': security_code,
            'security_name': security_name,
            'update_type': update_type
        }
        
        result = update_single_security.delay(security_info)
        print(f"已提交任务: {result.id}")
        return result.id
    
    def submit_batch_update(self, batch_size=10):
        """提交批量更新任务"""
        task_id = submit_batch_update(batch_size)
        print(f"已提交批量更新任务: {task_id}")
        return task_id
    
    def check_task_status(self, task_id):
        """检查任务状态"""
        result = check_task_result(task_id)
        print(f"任务状态: {result}")
        return result
    
    def wait_for_task(self, task_id, timeout=300):
        """等待任务完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.check_task_status(task_id)
            if result['ready']:
                return result
            time.sleep(5)
        
        print(f"任务 {task_id} 超时")
        return None
    
    def get_active_tasks(self):
        """获取活跃任务列表"""
        inspect = self.app.control.inspect()
        active_tasks = inspect.active()
        return active_tasks
    
    def cancel_task(self, task_id):
        """取消任务"""
        self.app.control.revoke(task_id, terminate=True)
        print(f"已取消任务: {task_id}")
    
    def get_queue_length(self):
        """获取队列长度"""
        inspect = self.app.control.inspect()
        reserved = inspect.reserved()
        return reserved


def demo_usage():
    """使用示例"""
    manager = SecurityTaskManager()
    
    print("=== Celery 证券数据更新任务管理示例 ===")
    
    # 1. 提交单个任务
    print("\n1. 提交单个证券更新任务...")
    task_id = manager.submit_single_update('000001', '平安银行', 'price')
    
    # 2. 检查任务状态
    print("\n2. 检查任务状态...")
    time.sleep(2)
    status = manager.check_task_status(task_id)
    
    # 3. 提交批量任务
    print("\n3. 提交批量更新任务...")
    batch_task_id = manager.submit_batch_update(5)
    
    # 4. 等待任务完成
    print("\n4. 等待任务完成...")
    result = manager.wait_for_task(task_id, timeout=60)
    
    if result and result['successful']:
        print(f"任务完成: {result['result']}")
    else:
        print("任务失败或超时")
    
    # 5. 查看活跃任务
    print("\n5. 查看活跃任务...")
    active_tasks = manager.get_active_tasks()
    print(f"活跃任务: {active_tasks}")
    
    # 6. 查看队列长度
    print("\n6. 查看队列长度...")
    queue_length = manager.get_queue_length()
    print(f"队列长度: {queue_length}")


def create_sample_update_table():
    """创建示例的更新任务表"""
    sql = """
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
    """
    
    return sql


def insert_sample_data():
    """插入示例数据"""
    sql = """
    INSERT INTO securities_update_queue (security_code, security_name, update_type, priority) VALUES
    ('000001', '平安银行', 'all', 1),
    ('000002', '万科A', 'price', 2),
    ('000858', '五粮液', 'all', 1),
    ('002415', '海康威视', 'technical', 0),
    ('300059', '东方财富', 'all', 1),
    ('600036', '招商银行', 'all', 2),
    ('600519', '贵州茅台', 'all', 3),
    ('600887', '伊利股份', 'volume', 0),
    ('000725', '京东方A', 'all', 1),
    ('002594', '比亚迪', 'all', 2);
    """
    
    return sql


if __name__ == '__main__':
    # 运行示例
    demo_usage()
