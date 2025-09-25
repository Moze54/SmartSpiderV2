import hashlib
import json
from typing import Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs
import re

from smart_spider.core.logger import logger


class RequestFingerprinter:
    """请求指纹识别器 - 用于生成请求的唯一指纹，实现去重"""

    def __init__(
        self,
        include_url: bool = True,
        include_method: bool = True,
        include_headers: bool = False,
        include_data: bool = True,
        ignore_params: Optional[list] = None,
        ignore_headers: Optional[list] = None,
        sort_parameters: bool = True
    ):
        self.include_url = include_url
        self.include_method = include_method
        self.include_headers = include_headers
        self.include_data = include_data
        self.ignore_params = set(ignore_params or [])
        self.ignore_headers = set(ignore_headers or [
            'User-Agent', 'Accept', 'Accept-Language', 'Accept-Encoding',
            'Connection', 'Upgrade-Insecure-Requests', 'Cache-Control',
            'Sec-Fetch-Dest', 'Sec-Fetch-Mode', 'Sec-Fetch-Site'
        ])
        self.sort_parameters = sort_parameters

    def generate_fingerprint(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """生成请求指纹"""
        try:
            fingerprint_parts = []

            # 包含方法
            if self.include_method:
                fingerprint_parts.append(f"METHOD:{method.upper()}")

            # 包含URL（标准化处理）
            if self.include_url:
                normalized_url = self._normalize_url(url)
                fingerprint_parts.append(f"URL:{normalized_url}")

            # 包含数据
            if self.include_data and data:
                normalized_data = self._normalize_data(data)
                if normalized_data:
                    fingerprint_parts.append(f"DATA:{normalized_data}")

            # 包含请求头
            if self.include_headers and headers:
                normalized_headers = self._normalize_headers(headers)
                if normalized_headers:
                    fingerprint_parts.append(f"HEADERS:{normalized_headers}")

            # 组合所有部分
            fingerprint_string = "|".join(fingerprint_parts)

            # 生成MD5哈希
            fingerprint = hashlib.md5(fingerprint_string.encode('utf-8')).hexdigest()

            logger.debug(f"生成请求指纹: {fingerprint} - {url}")
            return fingerprint

        except Exception as e:
            logger.error(f"生成请求指纹失败: {url} - {str(e)}")
            # 如果出错，返回URL的基础指纹
            return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _normalize_url(self, url: str) -> str:
        """标准化URL"""
        try:
            parsed = urlparse(url)

            # 标准化域名（小写）
            netloc = parsed.netloc.lower()

            # 标准化路径
            path = parsed.path
            if not path:
                path = '/'

            # 处理查询参数
            query_params = parse_qs(parsed.query)

            # 移除需要忽略的参数
            for param in self.ignore_params:
                query_params.pop(param, None)

            # 排序参数（如果需要）
            if self.sort_parameters:
                query_params = dict(sorted(query_params.items()))

            # 重新构建查询字符串
            query = urlencode(query_params, doseq=True)

            # 重新构建URL
            normalized_url = f"{parsed.scheme}://{netloc}{path}"
            if query:
                normalized_url += f"?{query}"

            return normalized_url

        except Exception as e:
            logger.error(f"标准化URL失败: {url} - {str(e)}")
            return url

    def _normalize_data(self, data: Dict[str, Any]) -> str:
        """标准化请求数据"""
        try:
            # 移除需要忽略的字段
            filtered_data = {k: v for k, v in data.items() if k not in self.ignore_params}

            # 排序（如果需要）
            if self.sort_parameters:
                filtered_data = dict(sorted(filtered_data.items()))

            # 转换为JSON字符串
            return json.dumps(filtered_data, sort_keys=True, ensure_ascii=False)

        except Exception as e:
            logger.error(f"标准化数据失败: {str(e)}")
            return str(data)

    def _normalize_headers(self, headers: Dict[str, str]) -> str:
        """标准化请求头"""
        try:
            # 过滤需要忽略的头部
            filtered_headers = {
                k.lower(): v for k, v in headers.items()
                if k.lower() not in {h.lower() for h in self.ignore_headers}
            }

            # 排序
            filtered_headers = dict(sorted(filtered_headers.items()))

            # 转换为JSON字符串
            return json.dumps(filtered_headers, sort_keys=True, ensure_ascii=False)

        except Exception as e:
            logger.error(f"标准化头部失败: {str(e)}")
            return str(headers)


class RequestDeduplicator:
    """请求去重器"""

    def __init__(
        self,
        fingerprinter: Optional[RequestFingerprinter] = None,
        storage_backend: str = 'memory',  # memory, redis, database
        max_size: int = 100000,
        ttl: Optional[int] = None  # 生存时间（秒）
    ):
        self.fingerprinter = fingerprinter or RequestFingerprinter()
        self.storage_backend = storage_backend
        self.max_size = max_size
        self.ttl = ttl

        # 内存存储
        self.seen_requests: Dict[str, dict] = {}
        self.request_order: list = []  # 用于LRU淘汰

        # Redis存储（如果配置）
        self.redis_client = None
        if storage_backend == 'redis':
            try:
                import redis
                self.redis_client = redis.Redis(decode_responses=True)
                self.redis_client.ping()
                logger.info("使用Redis作为去重存储后端")
            except Exception as e:
                logger.warning(f"Redis连接失败，使用内存存储: {str(e)}")
                self.storage_backend = 'memory'

    def is_duplicate(self, fingerprint: str) -> bool:
        """检查请求是否重复"""
        try:
            if self.storage_backend == 'redis' and self.redis_client:
                return self.redis_client.exists(f"request:{fingerprint}")
            else:
                # 内存存储
                if fingerprint in self.seen_requests:
                    # 检查TTL
                    if self.ttl:
                        import time
                        stored_time = self.seen_requests[fingerprint].get('timestamp', 0)
                        if time.time() - stored_time \u003e self.ttl:
                            self.remove_fingerprint(fingerprint)
                            return False
                    return True
                return False

        except Exception as e:
            logger.error(f"检查重复请求失败: {str(e)}")
            return False

    def add_fingerprint(self, fingerprint: str, metadata: Optional[Dict] = None):
        """添加请求指纹"""
        try:
            metadata = metadata or {}
            metadata['timestamp'] = int(__import__('time').time())

            if self.storage_backend == 'redis' and self.redis_client:
                key = f"request:{fingerprint}"
                self.redis_client.hset(key, mapping={k: str(v) for k, v in metadata.items()})
                if self.ttl:
                    self.redis_client.expire(key, self.ttl)

            else:
                # 内存存储
                self._evict_if_needed()

                self.seen_requests[fingerprint] = metadata
                self.request_order.append(fingerprint)

                # 记录日志
                logger.debug(f"添加请求指纹: {fingerprint}")

        except Exception as e:
            logger.error(f"添加请求指纹失败: {str(e)}")

    def remove_fingerprint(self, fingerprint: str):
        """移除请求指纹"""
        try:
            if self.storage_backend == 'redis' and self.redis_client:
                self.redis_client.delete(f"request:{fingerprint}")
            else:
                # 内存存储
                self.seen_requests.pop(fingerprint, None)
                if fingerprint in self.request_order:
                    self.request_order.remove(fingerprint)

        except Exception as e:
            logger.error(f"移除请求指纹失败: {str(e)}")

    def _evict_if_needed(self):
        """如果需要，淘汰旧的指纹"""
        if len(self.seen_requests) \u003e= self.max_size:
            # LRU淘汰 - 移除最久未使用的
            if self.request_order:
                oldest_fingerprint = self.request_order.pop(0)
                self.seen_requests.pop(oldest_fingerprint, None)
                logger.debug(f"LRU淘汰请求指纹: {oldest_fingerprint}")

    def get_stats(self) -> dict:
        """获取去重统计信息"""
        if self.storage_backend == 'redis' and self.redis_client:
            try:
                # 统计Redis中的指纹数量
                pattern = "request:*"
                cursor = 0
                count = 0

                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=pattern, count=1000)
                    count += len(keys)
                    if cursor == 0:
                        break

                return {
                    'backend': 'redis',
                    'total_fingerprints': count,
                    'max_size': self.max_size,
                    'ttl': self.ttl
                }
            except Exception as e:
                logger.error(f"获取Redis统计失败: {str(e)}")
                return {'error': str(e)}
        else:
            return {
                'backend': 'memory',
                'total_fingerprints': len(self.seen_requests),
                'max_size': self.max_size,
                'ttl': self.ttl
            }

    def clear_all(self):
        """清除所有指纹"""
        try:
            if self.storage_backend == 'redis' and self.redis_client:
                # 清除Redis中的所有指纹
                pattern = "request:*"
                cursor = 0

                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=pattern, count=1000)
                    if keys:
                        self.redis_client.delete(*keys)
                    if cursor == 0:
                        break

            else:
                # 内存存储
                self.seen_requests.clear()
                self.request_order.clear()

            logger.info("清除所有请求指纹")

        except Exception as e:
            logger.error(f"清除指纹失败: {str(e)}")


class SmartDeduplicator:
    """智能去重器 - 集成指纹生成和去重逻辑"""

    def __init__(
        self,
        fingerprinter: Optional[RequestFingerprinter] = None,
        storage_backend: str = 'memory',
        max_size: int = 100000,
        ttl: Optional[int] = None
    ):
        self.fingerprinter = fingerprinter or RequestFingerprinter()
        self.deduplicator = RequestDeduplicator(
            fingerprinter=self.fingerprinter,
            storage_backend=storage_backend,
            max_size=max_size,
            ttl=ttl
        )

    def should_skip_request(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """判断是否应该跳过请求（重复检测）"""
        try:
            # 生成指纹
            fingerprint = self.fingerprinter.generate_fingerprint(
                url=url,
                method=method,
                headers=headers,
                data=data,
                **kwargs
            )

            # 检查是否重复
            if self.deduplicator.is_duplicate(fingerprint):
                logger.info(f"检测到重复请求，跳过: {url}")
                return True

            # 添加指纹到去重器
            self.deduplicator.add_fingerprint(fingerprint, {
                'url': url,
                'method': method,
                'timestamp': int(__import__('time').time())
            })

            return False

        except Exception as e:
            logger.error(f"请求去重检查失败: {url} - {str(e)}")
            # 如果出错，不跳过请求
            return False

    def get_fingerprint(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """获取请求指纹"""
        return self.fingerprinter.generate_fingerprint(
            url=url,
            method=method,
            headers=headers,
            data=data,
            **kwargs
        )

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.deduplicator.get_stats()

    def clear_all(self):
        """清除所有指纹"""
        self.deduplicator.clear_all()\n\n# 全局智能去重器实例\nsmart_deduplicator = SmartDeduplicator()\n\n\ndef should_skip_duplicate_request(\n    url: str,\n    method: str = 'GET',\n    headers: Optional[Dict[str, str]] = None,\n    data: Optional[Dict[str, Any]] = None\n) -\u003e bool:\n    \"\"\"快捷函数 - 判断是否应该跳过重复请求\"\"\"\n    return smart_deduplicator.should_skip_request(url, method, headers, data)\n\n\ndef get_request_fingerprint(\n    url: str,\n    method: str = 'GET',\n    headers: Optional[Dict[str, str]] = None,\n    data: Optional[Dict[str, Any]] = None\n) -\u003e str:\n    \"\"\"快捷函数 - 获取请求指纹\"\"\"\n    return smart_deduplicator.get_fingerprint(url, method, headers, data)\n\n\ndef clear_request_fingerprints():\n    \"\"\"快捷函数 - 清除所有请求指纹\"\"\"\n    smart_deduplicator.clear_all()\n\n\ndef get_deduplication_stats() -\u003e dict:\n    \"\"\"快捷函数 - 获取去重统计信息\"\"\"\n    return smart_deduplicator.get_stats()\n\n\n# 配置示例\n# 基本配置（只检查URL）\nbasic_fingerprinter = RequestFingerprinter(
    include_url=True,
    include_method=False,
    include_headers=False,
    include_data=False
)\n\n# 严格配置（检查所有内容）\nstrict_fingerprinter = RequestFingerprinter(
    include_url=True,
    include_method=True,
    include_headers=True,
    include_data=True,
    ignore_params=['timestamp', 'nonce', 'signature'],
    ignore_headers=['User-Agent', 'Cookie']
)\n\n# API配置（忽略时间戳等动态参数）\napi_fingerprinter = RequestFingerprinter(
    include_url=True,
    include_method=True,
    include_headers=False,
    include_data=True,
    ignore_params=['timestamp', 't', '_', 'callback', 'random'],
    sort_parameters=True
)\n\n# 创建不同用途的去重器\nbasic_deduplicator = SmartDeduplicator(fingerprinter=basic_fingerprinter, max_size=10000)\nstrict_deduplicator = SmartDeduplicator(fingerprinter=strict_fingerprinter, max_size=5000)\napi_deduplicator = SmartDeduplicator(fingerprinter=api_fingerprinter, max_size=20000, ttl=3600)\n\n# 选择合适的去重器\ndef get_deduplicator_for_task(task_type: str = "basic") -\u003e SmartDeduplicator:\n    \"\"\"根据任务类型获取合适的去重器\"\"\"\n    deduplicators = {\n        \"basic\": basic_deduplicator,\n        \"strict\": strict_deduplicator,\n        \"api\": api_deduplicator,\n        \"default\": smart_deduplicator\n    }\n    return deduplicators.get(task_type, smart_deduplicator)\n\n\n# 导出常用函数\n__all__ = [\n    'RequestFingerprinter',\n    'RequestDeduplicator',\n    'SmartDeduplicator',\n    'smart_deduplicator',\n    'should_skip_duplicate_request',\n    'get_request_fingerprint',\n    'clear_request_fingerprints',\n    'get_deduplication_stats',\n    'get_deduplicator_for_task',\n    'basic_deduplicator',\n    'strict_deduplicator',\n    'api_deduplicator'\n]