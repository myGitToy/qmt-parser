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
echo 正在测试网络连接...
python test_network.py

echo.
echo 正在启动监控服务...
echo 如果无法访问localhost:8501，请尝试以下地址:
echo - http://127.0.0.1:8501
echo - http://0.0.0.0:8501
echo 按 Ctrl+C 停止服务
echo.

REM 启动Streamlit应用，允许外部访问
python -m streamlit run mysql_monitor.py --server.port 8501 --server.address 0.0.0.0 --server.headless false --browser.gatherUsageStats false --logger.level error

if errorlevel 1 (
    echo.
    echo 启动失败！故障排除建议:
    echo 1. 检查端口8501是否被占用
    echo 2. 尝试以管理员身份运行
    echo 3. 检查防火墙设置
    echo 4. 尝试其他端口: streamlit run mysql_monitor.py --server.port 8502
    echo.
)

pause
