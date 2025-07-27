@echo off
REM Celery 证券数据更新系统启动脚本 (Windows)
REM 
REM 用法: 
REM   start_celery.bat worker      - 启动 Worker
REM   start_celery.bat beat        - 启动 Beat
REM   start_celery.bat flower      - 启动 Flower
REM   start_celery.bat all         - 启动所有服务
REM   start_celery.bat test        - 测试配置
REM   start_celery.bat install     - 安装依赖

setlocal enabledelayedexpansion

REM 检查参数
if "%1"=="" (
    echo 用法: start_celery.bat [worker^|beat^|flower^|all^|test^|install]
    echo.
    echo   worker   - 启动 Celery Worker
    echo   beat     - 启动 Celery Beat
    echo   flower   - 启动 Flower 监控界面
    echo   all      - 启动所有服务
    echo   test     - 测试配置
    echo   install  - 安装依赖
    echo.
    exit /b 1
)

REM 设置环境变量
set PYTHONPATH=%CD%
set CELERY_APP=demo_celery

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python 未安装或未加入 PATH
    exit /b 1
)

REM 检查 .env 文件
if not exist .env (
    echo 警告: .env 文件不存在，正在复制示例文件...
    if exist .env.example (
        copy .env.example .env
        echo 已创建 .env 文件，请根据实际情况修改配置
    ) else (
        echo 错误: .env.example 文件不存在
        exit /b 1
    )
)

REM 根据参数执行相应操作
if "%1"=="install" (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖安装失败
        exit /b 1
    )
    echo 依赖安装完成
    goto :end
)

if "%1"=="test" (
    echo 正在测试配置...
    python test_config.py
    goto :end
)

if "%1"=="worker" (
    echo 启动 Celery Worker...
    celery -A %CELERY_APP% worker --loglevel=info --concurrency=4 --queues=securities_update,batch_update
    goto :end
)

if "%1"=="beat" (
    echo 启动 Celery Beat...
    celery -A %CELERY_APP% beat --loglevel=info
    goto :end
)

if "%1"=="flower" (
    echo 启动 Flower 监控界面...
    echo 访问地址: http://localhost:5555
    celery -A %CELERY_APP% flower --port=5555
    goto :end
)

if "%1"=="all" (
    echo 启动所有 Celery 服务...
    echo.
    echo 请在不同的命令行窗口中运行以下命令:
    echo   1. start_celery.bat worker
    echo   2. start_celery.bat beat
    echo   3. start_celery.bat flower
    echo.
    echo 或者使用 Python 脚本:
    echo   python start_celery.py all
    goto :end
)

echo 未知命令: %1
exit /b 1

:end
endlocal
