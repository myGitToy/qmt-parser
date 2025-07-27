@echo off
chcp 65001
echo =====================================================
echo        Celery 证券数据更新系统 - 快速启动脚本
echo =====================================================
echo.

echo 1. 检查环境配置...
python test_redis_connection.py
if %errorlevel% neq 0 (
    echo ❌ Redis 连接测试失败，请检查配置
    pause
    exit /b 1
)

echo.
echo 2. 选择启动模式:
echo    [1] 启动 Worker（处理任务）
echo    [2] 启动 Flower（监控界面）
echo    [3] 启动全部服务
echo    [4] 运行完整示例
echo    [5] 退出
echo.

set /p choice="请选择 (1-5): "

if "%choice%"=="1" (
    echo 启动 Celery Worker...
    python start_celery.py worker
) else if "%choice%"=="2" (
    echo 启动 Flower 监控界面...
    echo 访问 http://localhost:5555 查看监控界面
    python start_celery.py flower
) else if "%choice%"=="3" (
    echo 启动所有服务...
    python start_celery.py all
) else if "%choice%"=="4" (
    echo 运行完整示例...
    python complete_example.py
) else if "%choice%"=="5" (
    echo 退出程序
    exit /b 0
) else (
    echo 无效选择
    pause
    exit /b 1
)

pause
