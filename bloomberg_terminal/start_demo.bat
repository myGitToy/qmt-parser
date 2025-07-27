@echo off
title Bloomberg Terminal Demo
echo.
echo ================================================
echo            Bloomberg Terminal Demo
echo           金融数据终端演示平台
echo ================================================
echo.

echo [INFO] 检查环境...

if not exist "demo_simple.py" (
    echo [ERROR] 找不到 demo_simple.py 文件
    echo [ERROR] 请在 bloomberg_terminal 目录下运行
    pause
    exit /b 1
)

echo [INFO] 启动应用...
echo [INFO] 浏览器将打开: http://localhost:8501
echo [INFO] 按 Ctrl+C 停止应用
echo.

REM 简化启动命令
streamlit run demo_simple.py

echo.
echo [INFO] 应用已停止
pause

echo.
echo [INFO] 应用已停止
pause
