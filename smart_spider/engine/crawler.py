import asyncio
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from smart_spider.core.logger import crawler_logger
from smart_spider.core.exceptions import TaskConflictException, CrawlerException, NetworkException, TimeoutException
from smart_spider.engine.downloader import Downloader
from smart_spider.engine.parser import Parser
from smart_spider.config.crawler_config import TaskConfig
from smart_spider.models.database import TaskStatus


class CrawlerEngine:
    """爬虫引擎"""

    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, List[Dict]] = {}

    async def start_task(self, task_id: str, config: TaskConfig) -> str:
        """启动爬虫任务"""
        if task_id in self.active_tasks:
            raise TaskConflictException(f"任务 {task_id} 已在运行", task_id)

        if not config.urls:
            raise CrawlerException("没有提供爬取URL")

        crawler_logger.info(f"启动爬虫任务: {task_id}")

        # 创建任务
        task = asyncio.create_task(self._run_crawler(task_id, config))
        self.active_tasks[task_id] = task

        return task_id

    async def stop_task(self, task_id: str) -> bool:
        """停止爬虫任务"""
        if task_id not in self.active_tasks:
            return False

        task = self.active_tasks[task_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        del self.active_tasks[task_id]
        crawler_logger.info(f"停止爬虫任务: {task_id}")
        return True

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        if task_id not in self.active_tasks:
            return None

        return {
            'task_id': task_id,
            'status': 'running' if not self.active_tasks[task_id].done() else 'completed',
            'results_count': len(self.results.get(task_id, [])),
            'active_tasks': len(self.active_tasks)
        }

    async def get_task_results(self, task_id: str) -> List[Dict]:
        """获取任务结果"""
        return self.results.get(task_id, [])

    async def _run_crawler(self, task_id: str, config: TaskConfig) -> None:
        """运行爬虫"""
        try:
            crawler_logger.info(f"开始爬取任务: {task_id}")

            # 初始化结果容器
            self.results[task_id] = []

            # 创建下载器和解析器
            async with Downloader(config.crawler) as downloader:
                parser = Parser(config.parse)

                # 处理每个URL
                total_urls = len(config.urls)
                completed_count = 0

                for url in config.urls:
                    if task_id not in self.active_tasks:
                        crawler_logger.info(f"任务 {task_id} 被取消")
                        break

                    try:
                        # 下载页面
                        status_code, content, response_time = await downloader.download(
                            url=url,
                            method='GET'
                        )

                        if status_code == 200:
                            # 解析数据
                            parsed_data = parser.parse_html(content, url)

                            # 添加元数据
                            for item in parsed_data:
                                item.update({
                                    'task_id': task_id,
                                    'crawl_time': datetime.utcnow().isoformat(),
                                    'status_code': status_code,
                                    'response_time': response_time
                                })

                            self.results[task_id].extend(parsed_data)

                            crawler_logger.info(
                                f"爬取成功: {url}",
                                extra={
                                    'task_id': task_id,
                                    'url': url,
                                    'data_count': len(parsed_data)
                                }
                            )

                        else:
                            crawler_logger.warning(
                                f"HTTP错误: {status_code} - {url}",
                                extra={'task_id': task_id, 'url': url}
                            )

                    except Exception as e:
                        crawler_logger.error(
                            f"爬取失败: {url} - {str(e)}",
                            extra={'task_id': task_id, 'url': url}
                        )

                    completed_count += 1

                    # 检查是否达到最大数量限制
                    if config.max_items and len(self.results[task_id]) >= config.max_items:
                        crawler_logger.info(f"达到最大数量限制: {config.max_items}")
                        break

                crawler_logger.info(
                    f"任务 {task_id} 完成",
                    extra={
                        'task_id': task_id,
                        'total_urls': total_urls,
                        'completed_count': completed_count,
                        'results_count': len(self.results[task_id])
                    }
                )

        except asyncio.CancelledError:
            crawler_logger.info(f"任务 {task_id} 被取消")
            raise
        except Exception as e:
            crawler_logger.error(f"任务 {task_id} 失败: {str(e)}")
            raise
        finally:
            # 清理任务
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    async def get_active_tasks(self) -> List[str]:
        """获取活跃任务列表"""
        return list(self.active_tasks.keys())

    async def cleanup(self) -> None:
        """清理所有任务"""
        for task_id in list(self.active_tasks.keys()):
            await self.stop_task(task_id)

        self.results.clear()
        crawler_logger.info("所有任务已清理")


# 全局爬虫引擎实例
crawler_engine = CrawlerEngine()