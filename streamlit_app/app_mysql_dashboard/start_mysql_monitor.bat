@echo off
echo 启动MySQL数据库监控WebUI...
echo.

REM 检查是否安装了依赖
pip install -r requirements_monitor.txt

echo.
echo 正在启动Streamlit应用...
echo 应用将在浏览器中自动打开: http://localhost:8501
echo.

REM 启动Streamlit应用
streamlit run mysql_monitor.py --server.port 8501

pause
