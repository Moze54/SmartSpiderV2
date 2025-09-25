import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import aiofiles

from smart_spider.core.logger import logger


class FileStorage:
    """文件存储管理器"""

    def __init__(self, base_dir: str = "./storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.tasks_dir = self.base_dir / "tasks"
        self.results_dir = self.base_dir / "results"
        self.logs_dir = self.base_dir / "logs"

        for dir_path in [self.tasks_dir, self.results_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)

    async def save_task_config(self, task_id: str, config: Dict[str, Any]) -> str:
        """保存任务配置"""
        try:
            filepath = self.tasks_dir / f"{task_id}_config.json"

            config_data = {
                "task_id": task_id,
                "created_at": datetime.now().isoformat(),
                "config": config
            }

            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(config_data, ensure_ascii=False, indent=2))

            logger.info(f"任务配置已保存: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"保存任务配置失败: {str(e)}")
            raise

    async def save_task_results(self, task_id: str, results: List[Dict[str, Any]]) -> str:
        """保存任务结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.results_dir / f"{task_id}_results_{timestamp}.json"

            result_data = {
                "task_id": task_id,
                "export_time": datetime.now().isoformat(),
                "result_count": len(results),
                "results": results
            }

            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(result_data, ensure_ascii=False, indent=2))

            logger.info(f"任务结果已保存: {filepath} (记录数: {len(results)})")
            return str(filepath)

        except Exception as e:
            logger.error(f"保存任务结果失败: {str(e)}")
            raise

    async def save_task_log(self, task_id: str, log_content: str) -> str:
        """保存任务日志"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.logs_dir / f"{task_id}_log_{timestamp}.txt"

            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(log_content)

            logger.info(f"任务日志已保存: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"保存任务日志失败: {str(e)}")
            raise

    async def load_task_config(self, task_id: str) -> Optional[Dict[str, Any]]:
        """加载任务配置"""
        try:
            config_files = list(self.tasks_dir.glob(f"{task_id}_config.json"))

            if not config_files:
                return None

            # 获取最新的配置文件
            latest_config = max(config_files, key=lambda x: x.stat().st_mtime)

            async with aiofiles.open(latest_config, 'r', encoding='utf-8') as f:
                content = await f.read()
                config_data = json.loads(content)

            return config_data.get("config")

        except Exception as e:
            logger.error(f"加载任务配置失败: {str(e)}")
            return None

    async def load_task_results(self, task_id: str) -> List[Dict[str, Any]]:
        """加载任务结果"""
        try:
            result_files = list(self.results_dir.glob(f"{task_id}_results_*.json"))

            if not result_files:
                return []

            all_results = []
            for result_file in result_files:
                try:
                    async with aiofiles.open(result_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        result_data = json.loads(content)
                        all_results.extend(result_data.get("results", []))
                except Exception as e:
                    logger.warning(f"加载结果文件失败: {result_file} - {str(e)}")
                    continue

            return all_results

        except Exception as e:
            logger.error(f"加载任务结果失败: {str(e)}")
            return []

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            stats = {
                "total_size": 0,
                "file_counts": {
                    "configs": 0,
                    "results": 0,
                    "logs": 0
                },
                "latest_files": []
            }

            # 统计各类文件
            for category, dir_path in [
                ("configs", self.tasks_dir),
                ("results", self.results_dir),
                ("logs", self.logs_dir)
            ]:
                if dir_path.exists():
                    files = list(dir_path.iterdir())
                    stats["file_counts"][category] = len(files)

                    for file_path in files:
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            stats["total_size"] += file_size

                            stats["latest_files"].append({
                                "category": category,
                                "filename": file_path.name,
                                "size": file_size,
                                "modified_time": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })

            # 按修改时间排序，只保留最新的10个
            stats["latest_files"].sort(key=lambda x: x["modified_time"], reverse=True)
            stats["latest_files"] = stats["latest_files"][:10]

            # 转换文件大小为单位MB
            stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)

            return stats

        except Exception as e:
            logger.error(f"获取存储统计失败: {str(e)}")
            return {}

    def cleanup_old_files(self, days_to_keep: int = 30) -> int:
        """清理旧的文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            removed_count = 0

            for dir_path in [self.tasks_dir, self.results_dir, self.logs_dir]:
                if not dir_path.exists():
                    continue

                for file_path in dir_path.iterdir():
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            removed_count += 1
                            logger.info(f"删除旧文件: {file_path}")
                        except Exception as e:
                            logger.warning(f"删除文件失败: {file_path} - {str(e)}")

            logger.info(f"清理旧文件完成: 删除了 {removed_count} 个文件")
            return removed_count

        except Exception as e:
            logger.error(f"清理旧文件失败: {str(e)}")
            return 0


# 全局文件存储实例
file_storage = FileStorage()


async def save_task_data(
    task_id: str,
    config: Dict[str, Any],
    results: List[Dict[str, Any]],
    log_content: Optional[str] = None
) -> Dict[str, str]:
    """快捷保存任务数据"""
    saved_files = {}

    try:
        # 保存配置
        config_path = await file_storage.save_task_config(task_id, config)
        saved_files['config'] = config_path

        # 保存结果
        if results:
            results_path = await file_storage.save_task_results(task_id, results)
            saved_files['results'] = results_path

        # 保存日志
        if log_content:
            log_path = await file_storage.save_task_log(task_id, log_content)
            saved_files['log'] = log_path

        logger.info(f"任务数据保存完成: {task_id}")
        return saved_files

    except Exception as e:
        logger.error(f"保存任务数据失败: {task_id} - {str(e)}")
        raise