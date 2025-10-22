#!/bin/bash
# 电子试卷生成工具启动脚本（Linux/Mac）

echo "========================================"
echo "  电子试卷生成工具 v1.0"
echo "========================================"
echo ""
echo "正在启动程序..."
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 运行程序
python3 exam_generator.py

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "  程序运行出错！"
    echo "========================================"
    echo ""
    echo "请检查Python环境和依赖库"
    read -p "按Enter键退出..."
fi
