"""
MySQL数据库连接器
用于处理股票数据的MySQL存储操作
"""

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text, exc
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MySQLConnector:
    """MySQL数据库连接管理器"""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        初始化MySQL连接
        
        Args:
            config: 数据库配置字典，如果为None则从环境变量读取
        """
        self.logger = logging.getLogger(__name__)
        
        if config:
            self.config = config
        else:
            # 从环境变量读取配置
            self.config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'database': os.getenv('MYSQL_DATABASE', 'myfunds'),
                'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4')
            }
        
        self.engine = None
        self._connect()
    
    def _connect(self):
        """创建数据库连接"""
        try:
            # 构建连接字符串
            connection_string = (
                f"mysql+pymysql://{self.config['user']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}"
                f"/{self.config['database']}?charset={self.config['charset']}"
            )
            
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.logger.info("MySQL数据库连接成功")
            
        except Exception as e:
            self.logger.error(f"MySQL数据库连接失败: {str(e)}")
            raise
    
    def get_existing_data(self, 
                         code: str, 
                         ktype: str, 
                         start_date: str, 
                         end_date: str) -> pd.DataFrame:
        """
        获取现有数据（模仿akshare的数据库查询逻辑）
        
        Args:
            code: 证券代码
            ktype: K线类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            现有数据DataFrame
        """
        try:
            table_name = f'akshare_{ktype}'
            
            query = f"""
            SELECT code, date, open, close, high, low, volume, money 
            FROM {table_name} 
            WHERE date(date) BETWEEN '{start_date}' AND '{end_date}' 
            AND code = '{code}'
            ORDER BY date
            """
            
            df = pd.read_sql_query(query, self.engine)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except Exception as e:
            self.logger.error(f"查询现有数据失败: {str(e)}")
            return pd.DataFrame()
    
    def insert_data(self, 
                   data: pd.DataFrame, 
                   table_name: str, 
                   if_exists: str = 'append') -> int:
        """
        插入数据到MySQL（模仿akshare的数据写入逻辑）
        
        Args:
            data: 要插入的数据DataFrame
            table_name: 表名
            if_exists: 如果表存在的处理方式
            
        Returns:
            插入的记录数
        """
        try:
            if data.empty:
                return 0
            
            # 确保date列是datetime类型
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
            
            # 插入数据
            rows_inserted = data.to_sql(
                name=table_name,
                con=self.engine,
                index=False,
                if_exists=if_exists,
                method='multi',
                chunksize=1000
            )
            
            self.logger.info(f"成功插入 {len(data)} 条记录到表 {table_name}")
            return len(data)
            
        except Exception as e:
            self.logger.error(f"插入数据失败: {str(e)}")
            raise
    
    def create_table_if_not_exists(self, ktype: str):
        """
        如果表不存在则创建表
        
        Args:
            ktype: K线类型
        """
        table_name = f'akshare_{ktype}'
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(10) NOT NULL,
            date DATETIME NOT NULL,
            open DECIMAL(10,3) DEFAULT NULL,
            close DECIMAL(10,3) DEFAULT NULL,
            high DECIMAL(10,3) DEFAULT NULL,
            low DECIMAL(10,3) DEFAULT NULL,
            volume BIGINT DEFAULT NULL,
            money DECIMAL(15,2) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_code_date (code, date),
            INDEX idx_date (date),
            INDEX idx_code (code),
            UNIQUE KEY uk_code_date (code, date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AKShare {ktype} K线数据表';
        """
        
        try:
            with self.engine.begin() as conn:
                conn.execute(text(create_sql))
            self.logger.info(f"表 {table_name} 检查/创建完成")
        except Exception as e:
            self.logger.error(f"创建表 {table_name} 失败: {str(e)}")
            raise
    
    def get_table_info(self, ktype: str) -> Dict[str, Any]:
        """
        获取表信息
        
        Args:
            ktype: K线类型
            
        Returns:
            表信息字典
        """
        table_name = f'akshare_{ktype}'
        
        try:
            # 获取表行数
            count_sql = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = pd.read_sql_query(count_sql, self.engine)
            total_rows = count_result['count'].iloc[0]
            
            # 获取最新日期
            latest_sql = f"SELECT MAX(date) as latest_date FROM {table_name}"
            latest_result = pd.read_sql_query(latest_sql, self.engine)
            latest_date = latest_result['latest_date'].iloc[0]
            
            # 获取最早日期
            earliest_sql = f"SELECT MIN(date) as earliest_date FROM {table_name}"
            earliest_result = pd.read_sql_query(earliest_sql, self.engine)
            earliest_date = earliest_result['earliest_date'].iloc[0]
            
            # 获取唯一代码数
            codes_sql = f"SELECT COUNT(DISTINCT code) as unique_codes FROM {table_name}"
            codes_result = pd.read_sql_query(codes_sql, self.engine)
            unique_codes = codes_result['unique_codes'].iloc[0]
            
            return {
                'table_name': table_name,
                'total_rows': int(total_rows),
                'unique_codes': int(unique_codes),
                'latest_date': latest_date,
                'earliest_date': earliest_date,
                'date_range_days': (latest_date - earliest_date).days if latest_date and earliest_date else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取表 {table_name} 信息失败: {str(e)}")
            return {
                'table_name': table_name,
                'error': str(e)
            }
    
    def execute_custom_query(self, query: str) -> pd.DataFrame:
        """
        执行自定义查询
        
        Args:
            query: SQL查询语句
            
        Returns:
            查询结果DataFrame
        """
        try:
            df = pd.read_sql_query(query, self.engine)
            return df
        except Exception as e:
            self.logger.error(f"执行查询失败: {str(e)}")
            raise
    
    def backup_table(self, ktype: str, backup_suffix: str = None) -> str:
        """
        备份表
        
        Args:
            ktype: K线类型
            backup_suffix: 备份后缀，默认使用时间戳
            
        Returns:
            备份表名
        """
        source_table = f'akshare_{ktype}'
        
        if backup_suffix is None:
            backup_suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_table = f'{source_table}_backup_{backup_suffix}'
        
        try:
            backup_sql = f"CREATE TABLE {backup_table} AS SELECT * FROM {source_table}"
            
            with self.engine.begin() as conn:
                conn.execute(text(backup_sql))
            
            self.logger.info(f"表 {source_table} 备份为 {backup_table}")
            return backup_table
            
        except Exception as e:
            self.logger.error(f"备份表 {source_table} 失败: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        数据库健康检查
        
        Returns:
            健康状态信息
        """
        try:
            # 测试连接
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION() as version, NOW() as current_time"))
                row = result.fetchone()
                
                # 获取数据库状态
                status_result = conn.execute(text("SHOW STATUS LIKE 'Threads_connected'"))
                threads_connected = status_result.fetchone()[1]
                
                return {
                    'status': 'healthy',
                    'mysql_version': row[0],
                    'current_time': row[1],
                    'threads_connected': int(threads_connected),
                    'engine_pool_size': self.engine.pool.size(),
                    'engine_pool_checked_in': self.engine.pool.checkedin(),
                    'engine_pool_checked_out': self.engine.pool.checkedout()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("MySQL数据库连接已关闭")

# 上下文管理器支持
class MySQLContext:
    """MySQL数据库上下文管理器"""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        self.config = config
        self.connector = None
    
    def __enter__(self) -> MySQLConnector:
        self.connector = MySQLConnector(self.config)
        return self.connector
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connector:
            self.connector.close()

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 使用上下文管理器
    with MySQLContext() as db:
        # 健康检查
        health = db.health_check()
        print(f"数据库健康状态: {health}")
        
        # 创建测试表
        db.create_table_if_not_exists('1m')
        
        # 获取表信息
        table_info = db.get_table_info('1m')
        print(f"表信息: {table_info}")
        
        # 测试数据插入
        test_data = pd.DataFrame({
            'code': ['000001', '000002'],
            'date': [datetime.now(), datetime.now()],
            'open': [10.0, 11.0],
            'close': [10.5, 11.5],
            'high': [10.8, 11.8],
            'low': [9.8, 10.8],
            'volume': [1000000, 1100000],
            'money': [10500000.0, 12650000.0]
        })
        
        print("测试数据插入...")
        try:
            rows = db.insert_data(test_data, 'akshare_1m_test', 'replace')
            print(f"插入了 {rows} 条测试记录")
        except Exception as e:
            print(f"测试插入失败: {e}")
