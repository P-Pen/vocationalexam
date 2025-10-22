@echo off
chcp 65001 >nul
echo ========================================
echo   电子试卷生成工具 - 打包脚本
echo ========================================
echo.

echo [1/4] 检查环境...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误：未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [2/4] 安装 PyInstaller...
pip install pyinstaller

echo [3/4] 开始打包...
pyinstaller --clean ^
    --onefile ^
    --windowed ^
    --name="电子试卷生成工具" ^
    --add-data "static_template;static_template" ^
    --add-data "templates;templates" ^
    exam_generator.py

echo [4/4] 清理临时文件...
rmdir /s /q build 2>nul

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 生成的文件位于: dist\电子试卷生成工具.exe
echo.
echo 请将以下文件/文件夹复制到一起分发：
echo   - 电子试卷生成工具.exe
echo   - static_template\
echo   - templates\
echo   - README.md
echo   - 快速入门.md
echo   - 用户手册.md
echo   - examples\
echo.
pause
