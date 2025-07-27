@echo off
echo 启动Bloomberg Terminal Demo...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或未添加到PATH环境变量
    echo 请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查streamlit是否安装
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

echo 正在启动应用...
echo 应用将在浏览器中自动打开
echo 如果没有自动打开，请访问: http://localhost:8501
echo.
echo 按 Ctrl+C 停止应用

streamlit run app.py

pause
