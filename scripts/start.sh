#!/bin/bash
# SmartSpider 启动脚本

set -e

echo "🕷 启动 SmartSpider 系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 未安装"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "✗ requirements.txt 文件不存在"
    exit 1
fi

# 安装依赖
echo "正在安装依赖..."
pip3 install -r requirements.txt

# 初始化系统
echo "正在初始化系统..."
python3 -m smart_spider init

# 启动服务器
echo "正在启动服务器..."
python3 -m smart_spider server --host 0.0.0.0 --port 8000