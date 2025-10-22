@echo off
chcp 65001 >nul
echo ========================================
echo   电子试卷生成工具 v1.0
echo ========================================
echo.
echo 正在启动程序...
echo.

python exam_generator.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo   程序运行出错！
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 未安装Python或Python版本过低（需要3.8+）
    echo 2. Python未添加到系统PATH
    echo.
    echo 解决方案：
    echo 1. 访问 https://www.python.org/ 下载安装Python
    echo 2. 安装时勾选 "Add Python to PATH"
    echo.
    pause
)
