@echo off
REM SmartSpider 启动脚本 (Windows)

echo 🕷 启动 SmartSpider 系统...

REM 检查Python环境
where python > nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Python 未安装
    exit /b 1
)

REM 检查依赖
if not exist "requirements.txt" (
    echo ✗ requirements.txt 文件不存在
    exit /b 1
)

REM 安装依赖
echo 正在安装依赖...
pip install -r requirements.txt

REM 初始化系统
echo 正在初始化系统...
python -m smart_spider init

REM 启动服务器
echo 正在启动服务器...
python -m smart_spider server --host 0.0.0.0 --port 8000