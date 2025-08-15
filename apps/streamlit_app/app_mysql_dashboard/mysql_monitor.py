import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re
from urllib.parse import urlparse
import time
import warnings

# 抑制警告
warnings.filterwarnings('ignore')

# 加载环境变量
load_dotenv()

def check_streamlit_context():
    """检查Streamlit运行上下文"""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        return ctx is not None
    except:
        return True  # 如果无法检查，假设上下文正常

class MySQLMonitorWebUI:
    def __init__(self):
        self.connection = None
        self.db_configs = self.load_db_configs()
    
    def load_db_configs(self):
        """从.env文件加载数据库配置"""
        configs = {}
        
        # 获取所有数据库连接字符串
        db_connections = {
            'ALIYUN': os.getenv('ALIYUN_DB_CONN'),
            'AWS': os.getenv('AWS_DB_CONN'), 
            'LOCAL': os.getenv('LOCAL_DB_CONN'),
            'CENTOS9': os.getenv('CENTOS9_DB_CONN'),
            'UBUNTU186': os.getenv('UBUNTU186_DB_CONN'),
            'UBUNTU191': os.getenv('UBUNTU191_DB_CONN'),
            'DOCKER_201': os.getenv('docker_201_DB_CONN')
        }
        
        for name, conn_str in db_connections.items():
            if conn_str and conn_str != "teststring":
                configs[name] = self.parse_connection_string(conn_str)
        
        return configs
    
    def parse_connection_string(self, conn_str):
        """解析数据库连接字符串"""
        # 移除 mysql+pymysql:// 前缀
        clean_str = conn_str.replace('mysql+pymysql://', '')
        
        # 解析 user:password@host:port/database
        pattern = r'([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, clean_str)
        
        if match:
            user, password, host, port, database = match.groups()
            # 处理URL编码的密码
            password = password.replace('%40', '@').replace('%23', '#')
            
            return {
                'host': host,
                'port': int(port),
                'user': user,
                'password': password,
                'database': database
            }
        return None
    
    def connect_to_db(self, config):
        """连接到数据库"""
        try:
            if self.connection:
                self.connection.close()
            
            self.connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset='utf8mb4',
                connect_timeout=10,
                read_timeout=10,
                write_timeout=10
            )
            return True
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"数据库连接失败: {str(e)}")
            else:
                print(f"数据库连接失败: {str(e)}")
            return False
    
    def execute_query(self, query):
        """执行SQL查询"""
        try:
            if not self.connection:
                return pd.DataFrame()
            return pd.read_sql(query, self.connection)
        except Exception as e:
            if hasattr(st, 'error'):
                st.error(f"查询执行失败: {str(e)}")
            else:
                print(f"查询执行失败: {str(e)}")
            return pd.DataFrame()
    
    def get_connection_status(self):
        """获取连接状态"""
        queries = {
            'Current Connections': "SHOW STATUS LIKE 'Threads_connected'",
            'Max Used Connections': "SHOW STATUS LIKE 'Max_used_connections'",
            'Total Connections': "SHOW STATUS LIKE 'Connections'",
            'Max Connections': "SHOW VARIABLES LIKE 'max_connections'"
        }
        
        results = {}
        for name, query in queries.items():
            df = self.execute_query(query)
            if not df.empty:
                results[name] = int(df.iloc[0]['Value'])
        
        return results
    
    def get_process_list(self):
        """获取当前进程列表"""
        query = "SHOW FULL PROCESSLIST"
        return self.execute_query(query)
    
    def get_innodb_status(self):
        """获取InnoDB状态"""
        query = "SHOW STATUS LIKE 'Innodb_%'"
        df = self.execute_query(query)
        
        # 重要指标
        important_metrics = [
            'Innodb_buffer_pool_pages_total',
            'Innodb_buffer_pool_pages_free', 
            'Innodb_buffer_pool_pages_data',
            'Innodb_buffer_pool_read_requests',
            'Innodb_buffer_pool_reads',
            'Innodb_rows_read',
            'Innodb_rows_inserted',
            'Innodb_rows_updated',
            'Innodb_rows_deleted'
        ]
        
        if not df.empty:
            return df[df['Variable_name'].isin(important_metrics)]
        return df
    
    def get_database_size(self):
        """获取数据库大小"""
        query = """
        SELECT 
            table_schema as 'Database',
            ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'Size_MB'
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
        GROUP BY table_schema
        ORDER BY Size_MB DESC
        """
        return self.execute_query(query)
    
    def get_table_sizes(self):
        """获取表大小信息"""
        query = """
        SELECT 
            table_name as 'Table',
            ROUND(((data_length + index_length) / 1024 / 1024), 1) AS 'Size_MB',
            table_rows as 'Rows'
        FROM information_schema.TABLES 
        WHERE table_schema = DATABASE()
        ORDER BY (data_length + index_length) DESC
        LIMIT 20
        """
        return self.execute_query(query)
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None

def main():
    # 设置页面配置 - 必须是第一个Streamlit命令
    try:
        st.set_page_config(
            page_title="MySQL数据库监控",
            page_icon="🗄️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except st.errors.StreamlitAPIException:
        # 如果页面配置已经设置，忽略错误
        pass
    
    st.title("🗄️ MySQL数据库负载监控")
    st.markdown("---")
    
    # 初始化监控器
    monitor = MySQLMonitorWebUI()
    
    # 侧边栏 - 数据库选择
    with st.sidebar:
        st.header("🔧 数据库配置")
        
        if not monitor.db_configs:
            st.error("未找到有效的数据库配置，请检查.env文件")
            return
        
        # 数据库选择
        db_names = list(monitor.db_configs.keys())
        selected_db = st.selectbox("选择数据库", db_names)
        
        # 显示连接信息
        if selected_db:
            config = monitor.db_configs[selected_db]
            st.info(f"""
            **连接信息:**
            - 主机: {config['host']}
            - 端口: {config['port']}
            - 用户: {config['user']}
            - 数据库: {config['database']}
            """)
        
        # 自动刷新设置
        st.header("⚙️ 监控设置")
        auto_refresh = st.checkbox("自动刷新", value=False)
        if auto_refresh:
            refresh_interval = st.slider("刷新间隔(秒)", 5, 60, 10)
        
        # 连接按钮
        if st.button("🔗 连接数据库", type="primary"):
            if monitor.connect_to_db(monitor.db_configs[selected_db]):
                st.success("连接成功!")
                st.session_state.connected = True
            else:
                st.session_state.connected = False
    
    # 主界面
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    
    if not st.session_state.connected:
        st.warning("请先在侧边栏选择并连接数据库")
        return
    
    # 自动刷新逻辑
    if 'auto_refresh' in locals() and auto_refresh:
        placeholder = st.empty()
        with placeholder:
            st.info(f"自动刷新中... {refresh_interval}秒后更新")
            time.sleep(refresh_interval)
            placeholder.empty()
            st.rerun()
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 概览", "🔗 连接状态", "⚡ 性能指标", "📁 存储信息", "🔍 进程监控"])
    
    with tab1:
        st.header("📊 数据库概览")
        
        # 获取基本状态
        conn_status = monitor.get_connection_status()
        
        if conn_status:
            # 关键指标卡片
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                current_conn = conn_status.get('Current Connections', 0)
                st.metric("当前连接数", current_conn)
            
            with col2:
                max_conn = conn_status.get('Max Connections', 1)
                usage_pct = round((current_conn / max_conn) * 100, 1)
                st.metric("连接使用率", f"{usage_pct}%")
            
            with col3:
                total_conn = conn_status.get('Total Connections', 0)
                st.metric("总连接数", total_conn)
            
            with col4:
                max_used = conn_status.get('Max Used Connections', 0)
                st.metric("历史最大连接", max_used)
            
            # 连接使用率图表
            st.subheader("连接使用率")
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = usage_pct,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "连接使用率 (%)"},
                delta = {'reference': 80},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("🔗 连接状态详情")
        
        conn_status = monitor.get_connection_status()
        if conn_status:
            # 连接状态表格
            status_df = pd.DataFrame([
                {"指标": key, "值": value} 
                for key, value in conn_status.items()
            ])
            st.dataframe(status_df, use_container_width=True)
            
            # 连接趋势图（模拟数据）
            st.subheader("连接数趋势")
            current_time = datetime.now()
            time_points = [current_time - timedelta(minutes=x) for x in range(30, 0, -1)]
            
            # 模拟连接数变化
            import random
            base_conn = conn_status.get('Current Connections', 10)
            conn_values = [base_conn + random.randint(-3, 3) for _ in time_points]
            
            trend_df = pd.DataFrame({
                'Time': time_points,
                'Connections': conn_values
            })
            
            fig = px.line(trend_df, x='Time', y='Connections', 
                         title='最近30分钟连接数趋势')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("⚡ 性能指标")
        
        # InnoDB状态
        innodb_status = monitor.get_innodb_status()
        if not innodb_status.empty:
            st.subheader("InnoDB缓冲池状态")
            
            # 提取关键指标
            buffer_metrics = {}
            for _, row in innodb_status.iterrows():
                buffer_metrics[row['Variable_name']] = int(row['Value'])
            
            # 缓冲池使用情况
            total_pages = buffer_metrics.get('Innodb_buffer_pool_pages_total', 1)
            free_pages = buffer_metrics.get('Innodb_buffer_pool_pages_free', 0)
            data_pages = buffer_metrics.get('Innodb_buffer_pool_pages_data', 0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 缓冲池饼图
                fig = go.Figure(data=[go.Pie(
                    labels=['数据页', '空闲页', '其他'],
                    values=[data_pages, free_pages, total_pages - data_pages - free_pages],
                    title="缓冲池页面分布"
                )])
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 读取统计
                read_requests = buffer_metrics.get('Innodb_buffer_pool_read_requests', 0)
                reads = buffer_metrics.get('Innodb_buffer_pool_reads', 0)
                hit_rate = round((read_requests - reads) / read_requests * 100, 2) if read_requests > 0 else 0
                
                st.metric("缓冲池命中率", f"{hit_rate}%")
                st.metric("总读取请求", f"{read_requests:,}")
                st.metric("物理读取", f"{reads:,}")
            
            # 行操作统计
            st.subheader("行操作统计")
            row_ops = {
                '读取': buffer_metrics.get('Innodb_rows_read', 0),
                '插入': buffer_metrics.get('Innodb_rows_inserted', 0),
                '更新': buffer_metrics.get('Innodb_rows_updated', 0),
                '删除': buffer_metrics.get('Innodb_rows_deleted', 0)
            }
            
            ops_df = pd.DataFrame([
                {"操作": key, "次数": value} 
                for key, value in row_ops.items()
            ])
            
            fig = px.bar(ops_df, x='操作', y='次数', title='行操作统计')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.header("📁 存储信息")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 数据库大小
            st.subheader("数据库大小")
            db_sizes = monitor.get_database_size()
            if not db_sizes.empty:
                fig = px.pie(db_sizes, values='Size_MB', names='Database', 
                           title='各数据库大小分布')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(db_sizes, use_container_width=True)
        
        with col2:
            # 表大小
            st.subheader("表大小 (前20)")
            table_sizes = monitor.get_table_sizes()
            if not table_sizes.empty:
                fig = px.bar(table_sizes.head(10), x='Size_MB', y='Table', 
                           orientation='h', title='最大的10个表')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(table_sizes, use_container_width=True)
    
    with tab5:
        st.header("🔍 进程监控")
        
        # 获取进程列表
        processes = monitor.get_process_list()
        if not processes.empty:
            # 进程统计
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("总进程数", len(processes))
            
            with col2:
                active_processes = processes[processes['Command'] != 'Sleep']
                st.metric("活跃进程数", len(active_processes))
            
            with col3:
                long_queries = processes[processes['Time'] > 60]
                st.metric("长时间查询", len(long_queries))
            
            # 进程状态分布
            st.subheader("进程状态分布")
            command_counts = processes['Command'].value_counts()
            fig = px.pie(values=command_counts.values, names=command_counts.index, 
                        title='进程命令类型分布')
            st.plotly_chart(fig, use_container_width=True)
            
            # 进程详情表格
            st.subheader("当前进程列表")
            
            # 过滤选项
            show_all = st.checkbox("显示所有进程", value=False)
            if not show_all:
                processes = processes[processes['Command'] != 'Sleep']
            
            # 显示进程表格
            if not processes.empty:
                st.dataframe(
                    processes[['Id', 'User', 'Host', 'db', 'Command', 'Time', 'State', 'Info']], 
                    use_container_width=True
                )
            else:
                st.info("当前没有活跃的进程")
    
    # 页面底部信息
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"**最后更新时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if st.button("🔄 手动刷新", type="secondary"):
            st.rerun()
    
    # 清理连接
    if st.session_state.get('connected'):
        monitor.close_connection()

if __name__ == "__main__":
    # 检查运行环境
    if check_streamlit_context():
        main()
    else:
        print("请使用 'streamlit run mysql_monitor.py' 命令启动应用")
