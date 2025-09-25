"""
Cookie管理模块 - 基础版本
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from smart_spider.core.exceptions import CookieException
from smart_spider.core.logger import logger


class CookieManager:
    """Cookie管理器"""

    def __init__(self):
        self.cookies_dir = Path("cookies")
        self.cookies_dir.mkdir(exist_ok=True)

    def save_cookies(self, cookies: Dict[str, str], domain: str, source: str = "unknown") -> str:
        """保存Cookie到文件"""
        try:
            # 创建文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{domain}_{source}_{timestamp}.json"
            filepath = self.cookies_dir / filename

            # 准备Cookie数据
            cookie_data = {
                "domain": domain,
                "source": source,
                "cookies": cookies,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
            }

            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Cookie保存成功: {domain} -> {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Cookie保存失败: {domain}, 错误: {str(e)}")
            raise CookieException(f"Cookie保存失败: {str(e)}", domain=domain)

    def load_cookies(self, filepath: str) -> Dict[str, str]:
        """从文件加载Cookie"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)

            # 检查是否过期
            expires_at = datetime.fromisoformat(cookie_data["expires_at"])
            if datetime.now() > expires_at:
                logger.warning(f"Cookie文件已过期: {filepath}")
                return {}

            return cookie_data["cookies"]

        except Exception as e:
            logger.error(f"Cookie加载失败: {filepath}, 错误: {str(e)}")
            raise CookieException(f"Cookie加载失败: {str(e)}")

    def get_cookie_files(self, domain: str) -> List[Path]:
        """获取指定域名的Cookie文件"""
        cookie_files = []
        for cookie_file in self.cookies_dir.glob(f"{domain}_*.json"):
            if cookie_file.is_file():
                cookie_files.append(cookie_file)

        # 按修改时间排序，最新的在前
        cookie_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return cookie_files

    def filter_valid_cookies(self, domain: str) -> List[str]:
        """过滤有效的Cookie文件"""
        valid_files = []
        cookie_files = self.get_cookie_files(domain)

        for cookie_file in cookie_files:
            try:
                # 检查文件是否过期
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie_data = json.load(f)

                expires_at = datetime.fromisoformat(cookie_data["expires_at"])
                if datetime.now() <= expires_at:
                    valid_files.append(str(cookie_file))
                else:
                    logger.info(f"删除过期Cookie文件: {cookie_file}")
                    cookie_file.unlink()

            except Exception as e:
                logger.warning(f"Cookie文件无效: {cookie_file}, 错误: {str(e)}")
                # 删除无效文件
                try:
                    cookie_file.unlink()
                except:
                    pass

        return valid_files

    def get_browser_cookies(self, domain: str, browser: str = "chrome") -> Optional[Dict[str, str]]:
        """从浏览器获取Cookie (简化版本)"""
        try:
            # 这里可以实现从浏览器获取Cookie的逻辑
            # 由于需要额外的依赖，这里返回空值
            logger.info(f"尝试从{browser}浏览器获取{domain}的Cookie")
            return None
        except Exception as e:
            logger.error(f"从浏览器获取Cookie失败: {domain}, 错误: {str(e)}")
            return None

    def get_cookie_stats(self) -> Dict[str, Any]:
        """获取Cookie统计信息"""
        cookie_files = list(self.cookies_dir.glob("*.json"))
        total_cookies = 0
        valid_cookies = 0
        expired_cookies = 0

        for cookie_file in cookie_files:
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie_data = json.load(f)

                total_cookies += 1
                expires_at = datetime.fromisoformat(cookie_data["expires_at"])

                if datetime.now() <= expires_at:
                    valid_cookies += 1
                else:
                    expired_cookies += 1

            except Exception as e:
                logger.warning(f"统计Cookie文件失败: {cookie_file}, 错误: {str(e)}")

        return {
            "total_files": len(cookie_files),
            "total_cookies": total_cookies,
            "valid_cookies": valid_cookies,
            "expired_cookies": expired_cookies
        }

    def cleanup_expired_cookies(self) -> int:
        """清理过期的Cookie"""
        removed_count = 0
        cookie_files = list(self.cookies_dir.glob("*.json"))

        for cookie_file in cookie_files:
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie_data = json.load(f)

                expires_at = datetime.fromisoformat(cookie_data["expires_at"])
                if datetime.now() > expires_at:
                    cookie_file.unlink()
                    removed_count += 1
                    logger.info(f"删除过期Cookie文件: {cookie_file}")

            except Exception as e:
                logger.warning(f"清理Cookie文件失败: {cookie_file}, 错误: {str(e)}")

        return removed_count


# 全局Cookie管理器实例
cookie_manager = CookieManager()


# 快捷函数
def get_cookie_statistics() -> Dict[str, Any]:
    """获取Cookie统计信息"""
    return cookie_manager.get_cookie_stats()


def filter_valid_cookies(domain: str) -> List[str]:
    """过滤有效的Cookie文件"""
    return cookie_manager.filter_valid_cookies(domain)


def cleanup_expired_cookies() -> int:
    """清理过期的Cookie"""
    return cookie_manager.cleanup_expired_cookies()


__all__ = [
    'CookieManager',
    'cookie_manager',
    'get_cookie_statistics',
    'filter_valid_cookies',
    'cleanup_expired_cookies'
]