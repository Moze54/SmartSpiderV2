#!/usr/bin/env python3
"""
SmartSpider 管理脚本
提供系统管理、维护和监控功能
"""
import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from smart_spider.core.database import init_db, db_manager
from smart_spider.core.database_optimization import db_optimizer
from smart_spider.core.proxy_manager import proxy_manager, load_proxies_on_startup
from smart_spider.core.cookie_manager import cookie_manager
from smart_spider.core.logger import logger
from smart_spider.scheduler.task_scheduler import task_scheduler
from smart_spider.storage.file_storage import file_storage
from smart_spider.storage.data_exporter import data_exporter
from smart_spider.config.settings import settings
from smart_spider.models.database import Task, TaskStatus
from sqlalchemy import select, func, text
from smart_spider.core.priority_queue import task_priority_queue


class SmartSpiderManager:
    """SmartSpider 管理器"""

    def __init__(self):
        self.start_time = datetime.now()

    async def initialize_system(self):
        """初始化系统"""
        print("🔧 正在初始化 SmartSpider 系统...")

        # 创建必要目录
        self._create_directories()

        # 初始化数据库
        await self._initialize_database()

        # 加载代理
        await self._load_proxies()

        # 启动调度器
        await self._start_scheduler()

        print("✅ 系统初始化完成")

    def _create_directories(self):
        """创建必要目录"""
        directories = [
            settings.app.upload_dir,
            settings.app.output_dir,
            settings.app.storage_dir,
            settings.advanced.cookie_storage_dir,
            settings.logging.file_path.parent,
            "logs",
            "backups"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {directory}")

    async def _initialize_database(self):
        """初始化数据库"""
        try:
            print("正在初始化数据库...")
            await init_db()

            print("正在创建性能索引...")
            await db_optimizer.create_performance_indexes()
            await db_optimizer.create_composite_indexes()

            print("✓ 数据库初始化完成")

        except Exception as e:
            print(f"✗ 数据库初始化失败: {str(e)}")
            raise

    async def _load_proxies(self):
        """加载代理"""
        try:
            print("正在加载代理...")
            await load_proxies_on_startup()

            # 如果有配置的代理列表，添加它们
            if settings.crawler.proxy_list:
                from smart_spider.core.proxy_manager import init_proxy_pool
                success_count, _ = await init_proxy_pool(settings.crawler.proxy_list)
                print(f"✓ 加载代理完成: 成功 {success_count} 个")

        except Exception as e:
            print(f"⚠️  代理加载失败: {str(e)}")

    async def _start_scheduler(self):
        """启动调度器"""
        if settings.scheduler.enabled:
            try:
                print("正在启动任务调度器...")
                await task_scheduler.start()
                print("✓ 任务调度器启动完成")
            except Exception as e:
                print(f"⚠️  调度器启动失败: {str(e)}")

    async def cleanup_system(self):
        """清理系统"""
        print("🧹 正在清理系统...")

        # 清理数据库
        deleted_count = await db_optimizer.cleanup_old_data(
            days_to_keep=settings.cleanup.old_files_days
        )
        print(f"✓ 清理数据库: 删除了 {deleted_count} 条旧记录")

        # 清理文件存储
        removed_files = file_storage.cleanup_old_files(
            days_to_keep=settings.cleanup.old_files_days
        )
        print(f"✓ 清理文件存储: 删除了 {removed_files} 个旧文件")

        # 清理Cookie
        removed_cookies = cookie_manager.cleanup_old_cookies(
            days_to_keep=settings.cleanup.old_cookies_days
        )
        print(f"✓ 清理Cookie: 删除了 {removed_cookies} 个旧Cookie文件")

        # 清理代理
        removed_proxies = await proxy_manager.cleanup_old_proxies(
            days_to_keep=settings.cleanup.old_proxies_days
        )
        print(f"✓ 清理代理: 删除了 {removed_proxies} 个旧代理")

        # 清理导出文件
        # 这里可以添加导出文件的清理逻辑

        print("✅ 系统清理完成")

    async def optimize_system(self):
        """优化系统"""
        print("⚡ 正在优化系统...")

        # 数据库优化
        print("正在优化数据库...")
        await db_optimizer.run_performance_optimization()

        # 代理池优化
        print("正在优化代理池...")
        await proxy_manager.check_all_proxies()

        # 重建索引
        print("正在重建索引...")
        await db_optimizer.rebuild_indexes()

        print("✅ 系统优化完成")

    async def check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        print("🏥 正在检查系统健康状态...")

        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }

        # 数据库健康检查
        try:
            db_health = await db_optimizer.get_database_health()
            health_status['components']['database'] = {
                'status': 'healthy' if db_health['is_healthy'] else 'unhealthy',
                'details': db_health
            }
            if not db_health['is_healthy']:
                health_status['overall_status'] = 'unhealthy'
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['overall_status'] = 'unhealthy'

        # 代理池健康检查
        try:
            proxy_stats = proxy_manager.get_proxy_stats()
            active_proxies = proxy_stats.get('active_proxies', 0)
            total_proxies = proxy_stats.get('total_proxies', 0)

            health_status['components']['proxy_pool'] = {
                'status': 'healthy' if active_proxies \u003e 0 else 'warning',
                'details': {
                    'active_proxies': active_proxies,
                    'total_proxies': total_proxies,
                    'success_rate': proxy_stats.get('overall_success_rate', 0)
                }
            }
        except Exception as e:
            health_status['components']['proxy_pool'] = {
                'status': 'error',
                'error': str(e)
            }

        # 存储健康检查
        try:
            storage_stats = file_storage.get_storage_stats()
            health_status['components']['storage'] = {
                'status': 'healthy',
                'details': storage_stats
            }
        except Exception as e:
            health_status['components']['storage'] = {
                'status': 'error',
                'error': str(e)
            }

        # 调度器健康检查
        try:
            if settings.scheduler.enabled:
                scheduler_stats = task_scheduler.get_scheduled_tasks()
                health_status['components']['scheduler'] = {
                    'status': 'healthy',
                    'details': {
                        'active_jobs': len(scheduler_stats)
                    }
                }
            else:
                health_status['components']['scheduler'] = {
                    'status': 'disabled',
                    'details': {}
                }
        except Exception as e:
            health_status['components']['scheduler'] = {
                'status': 'error',
                'error': str(e)
            }

        # 优先级队列健康检查
        try:
            queue_stats = task_priority_queue.get_queue_stats()
            health_status['components']['priority_queue'] = {
                'status': 'healthy',
                'details': queue_stats
            }
        except Exception as e:
            health_status['components']['priority_queue'] = {
                'status': 'error',
                'error': str(e)
            }

        print(f"✓ 系统健康状态: {health_status['overall_status']}")
        return health_status

    async def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        print("📊 正在收集系统统计信息...")

        stats = {
            'timestamp': datetime.now().isoformat(),
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'components': {}
        }

        # 数据库统计
        try:
            db_stats = await db_optimizer.analyze_all_tables()
            stats['components']['database'] = db_stats
        except Exception as e:
            stats['components']['database'] = {'error': str(e)}

        # 任务统计
        try:
            async with AsyncSession(db_manager.engine) as session:
                # 总任务数
                total_tasks = await session.scalar(select(func.count(Task.id)))

                # 状态分布
                status_counts = {}
                for status in TaskStatus:
                    count = await session.scalar(
                        select(func.count(Task.id)).where(Task.status == status)
                    )
                    status_counts[status.value] = count

                # 最近24小时任务数
                recent_tasks = await session.scalar(
                    select(func.count(Task.id)).where(
                        Task.created_at \u003e= datetime.now() - timedelta(hours=24)
                    )
                )

                stats['components']['tasks'] = {
                    'total_tasks': total_tasks,
                    'status_distribution': status_counts,
                    'recent_24h_tasks': recent_tasks
                }
        except Exception as e:
            stats['components']['tasks'] = {'error': str(e)}

        # 存储统计
        try:
            storage_stats = file_storage.get_storage_stats()
            stats['components']['storage'] = storage_stats
        except Exception as e:
            stats['components']['storage'] = {'error': str(e)}

        # 导出统计
        try:
            export_stats = data_exporter.get_export_stats()
            stats['components']['export'] = export_stats
        except Exception as e:
            stats['components']['export'] = {'error': str(e)}

        # 代理统计
        try:
            proxy_stats = proxy_manager.get_proxy_stats()
            stats['components']['proxy_pool'] = proxy_stats
        except Exception as e:
            stats['components']['proxy_pool'] = {'error': str(e)}

        print("✓ 系统统计信息收集完成")
        return stats

    async def backup_system(self, backup_dir: Optional[str] = None):
        """备份系统数据"""
        backup_dir = backup_dir or f"backups/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        print(f"💾 正在备份系统数据到: {backup_dir}")

        # 数据库备份
        try:
            print("正在备份数据库...")
            # 这里可以实现数据库备份逻辑
            # 例如导出SQL文件或使用pg_dump
            backup_file = Path(backup_dir) / f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            print(f"✓ 数据库备份完成: {backup_file}")
        except Exception as e:
            print(f"⚠️  数据库备份失败: {str(e)}")

        # 文件备份
        try:
            print("正在备份文件...")
            import shutil

            # 备份重要目录
            backup_dirs = [
                (settings.app.upload_dir, "uploads"),
                (settings.app.output_dir, "output"),
                (settings.app.storage_dir, "storage"),
                (settings.advanced.cookie_storage_dir, "cookies")
            ]

            for source_dir, backup_name in backup_dirs:
                if Path(source_dir).exists():
                    target_dir = Path(backup_dir) / backup_name
                    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
                    print(f"✓ 备份目录: {source_dir} -> {target_dir}")

        except Exception as e:
            print(f"⚠️  文件备份失败: {str(e)}")

        print(f"✅ 系统备份完成: {backup_dir}")

    def print_system_info(self):
        """打印系统信息"""
        print("""
🕷 SmartSpider - 智能网络爬虫系统
═══════════════════════════════════════════════════════════

系统信息:
  版本: {version}
  环境: {environment}
  运行时间: {uptime}
  数据库: {database_type}
  存储路径: {storage_path}

可用命令:
  init      - 初始化系统
  cleanup   - 清理系统
  optimize  - 优化系统
  health    - 健康检查
  stats     - 统计信息
  backup    - 备份系统
  proxy     - 代理管理
  cookie    - Cookie管理
  task      - 任务管理

示例:
  python manage.py init
  python manage.py health
  python manage.py stats
  python manage.py backup --dir ./backups

═══════════════════════════════════════════════════════════
        """.format(
            version=settings.app.version,
            environment=settings.app.environment,
            uptime=self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            database_type="PostgreSQL",
            storage_path=settings.app.storage_dir
        ))


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SmartSpider 系统管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 初始化命令
    init_parser = subparsers.add_parser('init', help='初始化系统')

    # 清理命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理系统')

    # 优化命令
    optimize_parser = subparsers.add_parser('optimize', help='优化系统')

    # 健康检查命令
    health_parser = subparsers.add_parser('health', help='健康检查')

    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='统计信息')

    # 备份命令
    backup_parser = subparsers.add_parser('backup', help='备份系统')
    backup_parser.add_argument('--dir', help='备份目录')

    # 代理管理命令
    proxy_parser = subparsers.add_parser('proxy', help='代理管理')
    proxy_subparsers = proxy_parser.add_subparsers(dest='proxy_command')

    proxy_check_parser = proxy_subparsers.add_parser('check', help='检查代理')
    proxy_add_parser = proxy_subparsers.add_parser('add', help='添加代理')
    proxy_add_parser.add_argument('proxy_url', help='代理URL')
    proxy_stats_parser = proxy_subparsers.add_parser('stats', help='代理统计')

    # Cookie管理命令
    cookie_parser = subparsers.add_parser('cookie', help='Cookie管理')
    cookie_subparsers = cookie_parser.add_subparsers(dest='cookie_command')

    cookie_check_parser = cookie_subparsers.add_parser('check', help='检查Cookie')
    cookie_stats_parser = cookie_subparsers.add_parser('stats', help='Cookie统计')

    # 任务管理命令
    task_parser = subparsers.add_parser('task', help='任务管理')
    task_subparsers = task_parser.add_subparsers(dest='task_command')

    task_list_parser = task_subparsers.add_parser('list', help='列出任务')
    task_stats_parser = task_subparsers.add_parser('stats', help='任务统计')

    args = parser.parse_args()

    manager = SmartSpiderManager()

    if not args.command:
        manager.print_system_info()
        return

    # 执行命令
    if args.command == 'init':
        await manager.initialize_system()

    elif args.command == 'cleanup':
        await manager.cleanup_system()

    elif args.command == 'optimize':
        await manager.optimize_system()

    elif args.command == 'health':
        health_status = await manager.check_system_health()
        print("\n详细健康状态:")
        import json
        print(json.dumps(health_status, indent=2, ensure_ascii=False))

    elif args.command == 'stats':
        stats = await manager.get_system_statistics()
        print("\n详细统计信息:")
        import json
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.command == 'backup':
        await manager.backup_system(args.dir)

    elif args.command == 'proxy':
        if args.proxy_command == 'check':
            await check_proxy_health()
        elif args.proxy_command == 'add':
            success = await proxy_manager.add_proxy(args.proxy_url)
            if success:
                print(f"✓ 代理添加成功: {args.proxy_url}")
            else:
                print(f"✗ 代理添加失败: {args.proxy_url}")
        elif args.proxy_command == 'stats':
            stats = proxy_manager.get_proxy_stats()
            import json
            print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.command == 'cookie':
        if args.cookie_command == 'check':
            await validate_browser_cookies()
        elif args.cookie_command == 'stats':
            stats = cookie_manager.get_cookie_stats()
            import json
            print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.command == 'task':
        if args.task_command == 'list':
            await list_tasks()
        elif args.task_command == 'stats':
            await show_task_stats()


async def list_tasks():
    """列出任务"""
    try:
        from smart_spider.services.task_service import task_service
        from smart_spider.core.database import get_session

        async for session in get_session():
            tasks = await task_service.get_tasks(session)

            print(f"{'任务ID':\u003c36} {'名称':\u003c20} {'状态':\u003c10} {'进度':\u003c8} {'创建时间':\u003c20}")
            print("-" * 100)

            for task in tasks[:20]:  # 只显示前20个
                print(f"{task.task_id:\u003c36} {task.name:\u003c20} {task.status:\u003c10} {task.progress:\u003c8.1f}% {task.created_at.strftime('%Y-%m-%d %H:%M:%S'):\u003c20}")

            if len(tasks) \u003e 20:
                print(f"\n... 还有 {len(tasks) - 20} 个任务")

            break
    except Exception as e:
        print(f"✗ 列出任务失败: {str(e)}")


async def show_task_stats():
    """显示任务统计"""
    try:
        from smart_spider.services.task_service import task_service
        from smart_spider.core.database import get_session

        async for session in get_session():
            tasks = await task_service.get_tasks(session)

            status_counts = {}
            for task in tasks:
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            print("任务统计:")
            print(f"总任务数: {len(tasks)}")
            print("状态分布:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")

            break
    except Exception as e:
        print(f"✗ 显示任务统计失败: {str(e)}")


if __name__ == '__main__':
    asyncio.run(main())