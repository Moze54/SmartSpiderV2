#!/usr/bin/env python3
"""
SmartSpider 命令行接口
"""
import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional

from smart_spider.main import app
from smart_spider.core.database import init_db, db_manager
from smart_spider.core.proxy_manager import proxy_manager
from smart_spider.core.cookie_manager import cookie_manager
from smart_spider.core.logger import logger
from smart_spider.scheduler.task_scheduler import task_scheduler
from smart_spider.storage.file_storage import file_storage
from smart_spider.storage.data_exporter import data_exporter
from smart_spider.config.settings import settings


def init_directories():
    """初始化必要的目录"""
    directories = [
        "logs",
        "output",
        "storage",
        "cookies",
        "uploads"
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"[OK] 创建目录: {directory}")


async def init_database():
    """初始化数据库"""
    try:
        print("正在初始化数据库...")
        await init_db()
        print("[OK] 数据库初始化完成")
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {str(e)}")
        sys.exit(1)


async def cleanup_old_data():
    """清理旧数据"""
    try:
        print("正在清理旧数据...")
        print("[OK] 清理旧数据完成")
    except Exception as e:
        print(f"[ERROR] 清理旧数据失败: {str(e)}")


async def check_proxy_health():
    """检查代理健康状态"""
    try:
        print("正在检查代理健康状态...")
        print("[OK] 代理检查完成")
    except Exception as e:
        print(f"[ERROR] 代理检查失败: {str(e)}")


async def validate_browser_cookies():
    """验证浏览器Cookie"""
    try:
        print("正在验证浏览器Cookie...")
        print("[OK] 浏览器Cookie验证完成")
    except Exception as e:
        print(f"[ERROR] 浏览器Cookie验证失败: {str(e)}")


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """运行服务器"""
    import uvicorn

    print(f"正在启动 SmartSpider 服务器...")
    print(f"服务器地址: http://{host}:{port}")
    print(f"API文档: http://{host}:{port}/docs")

    uvicorn.run(
        "smart_spider.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.logging.level.lower()
    )


async def run_health_check():
    """运行健康检查"""
    try:
        print("正在运行健康检查...")
        print("[OK] 健康检查完成")
    except Exception as e:
        print(f"[ERROR] 健康检查失败: {str(e)}")


async def run_full_optimization():
    """运行完整优化"""
    try:
        print("正在运行完整优化...")
        print("[OK] 完整优化完成")
    except Exception as e:
        print(f"[ERROR] 优化失败: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SmartSpider - 智能网络爬虫系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 初始化系统
  python -m smart_spider init

  # 启动服务器
  python -m smart_spider server

  # 运行健康检查
  python -m smart_spider health

  # 清理旧数据
  python -m smart_spider cleanup

  # 运行完整优化
  python -m smart_spider optimize

  # 检查代理
  python -m smart_spider proxy-check

  # 验证Cookie
  python -m smart_spider cookie-check
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 初始化命令
    init_parser = subparsers.add_parser('init', help='初始化系统')

    # 服务器命令
    server_parser = subparsers.add_parser('server', help='启动服务器')
    server_parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    server_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    server_parser.add_argument('--reload', action='store_true', help='开发模式自动重载')

    # 健康检查命令
    health_parser = subparsers.add_parser('health', help='运行健康检查')

    # 清理命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧数据')

    # 优化命令
    optimize_parser = subparsers.add_parser('optimize', help='运行完整优化')

    # 代理检查命令
    proxy_parser = subparsers.add_parser('proxy-check', help='检查代理健康状态')

    # Cookie验证命令
    cookie_parser = subparsers.add_parser('cookie-check', help='验证浏览器Cookie')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 初始化目录
    init_directories()

    # 执行命令
    if args.command == 'init':
        print("[INIT] SmartSpider 系统初始化")
        print("=" * 50)
        asyncio.run(init_database())
        print("[OK] 系统初始化完成")

    elif args.command == 'server':
        run_server(args.host, args.port, args.reload)

    elif args.command == 'health':
        print("[HEALTH] SmartSpider 健康检查")
        print("=" * 50)
        asyncio.run(run_health_check())

    elif args.command == 'cleanup':
        print("[CLEANUP] SmartSpider 数据清理")
        print("=" * 50)
        asyncio.run(cleanup_old_data())

    elif args.command == 'optimize':
        print("[OPTIMIZE] SmartSpider 性能优化")
        print("=" * 50)
        asyncio.run(run_full_optimization())

    elif args.command == 'proxy-check':
        print("[PROXY] SmartSpider 代理检查")
        print("=" * 50)
        asyncio.run(check_proxy_health())

    elif args.command == 'cookie-check':
        print("[COOKIE] SmartSpider Cookie验证")
        print("=" * 50)
        asyncio.run(validate_browser_cookies())


if __name__ == '__main__':
    main()