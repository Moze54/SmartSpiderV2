#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import asyncio
import os
from pathlib import Path

import aiomysql
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from smart_spider.models.database import *
from smart_spider.config.settings import settings


async def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    try:
        conn = await aiomysql.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.user,
            password=settings.database.password,
            charset='utf8mb4'
        )

        async with conn.cursor() as cursor:
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {settings.database.name} \
                CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )

        await conn.commit()
        await conn.close()

        print(f"✅ 数据库 {settings.database.name} 创建/确认成功")

    except Exception as e:
        print(f"❌ 创建数据库失败: {str(e)}")
        raise


async def create_tables():
    """创建数据库表"""
    try:
        # 创建异步引擎
        engine = create_async_engine(
            f"mysql+aiomysql://{settings.database.user}:{settings.database.password}@"
            f"{settings.database.host}:{settings.database.port}/{settings.database.name}",
            echo=True
        )

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        await engine.dispose()

        print("✅ 数据表创建成功")

    except Exception as e:
        print(f"❌ 创建数据表失败: {str(e)}")
        raise


async def main():
    """主函数"""
    print("🚀 开始初始化SmartSpider数据库...")

    try:
        await create_database_if_not_exists()
        await create_tables()
        print("🎉 数据库初始化完成！")

    except Exception as e:
        print(f"💥 数据库初始化失败: {str(e)}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())