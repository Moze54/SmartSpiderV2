#!/usr/bin/env python3
"""
SmartSpider 启动脚本
"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # 确保必要的目录存在
    Path("logs").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

    # 启动应用
    uvicorn.run(
        "smart_spider.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )