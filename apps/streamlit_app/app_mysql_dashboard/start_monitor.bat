@echo off
title MySQL数据库监控WebUI
color 0A

echo ===============================================
echo           MySQL数据库监控WebUI
echo ===============================================
echo.

REM 设置环境变量以减少警告
set STREAMLIT_LOGGER_LEVEL=error
set STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false

echo 正在检查依赖包...
python -m pip install -q streamlit pandas pymysql plotly python-dotenv

echo.
echo 正在启动监控服务...
echo 访问地址: http://localhost:8501
echo 按 Ctrl+C 停止服务
echo.

REM 启动Streamlit应用
python -m streamlit run mysql_monitor.py --server.port 8501 --server.headless false --browser.gatherUsageStats false --logger.level error

pause
