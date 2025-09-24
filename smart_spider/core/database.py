from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from smart_spider.config.simple_config import database_config

# 数据库连接池配置
DATABASE_URL = database_config.url

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal

    async def create_tables(self):
        """创建所有表"""
        await init_db()

    async def drop_tables(self):
        """删除所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        async with self.session_factory() as session:
            yield session

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute("SELECT 1")
                return True
        except Exception:
            return False


# 全局数据库管理器实例
db_manager = DatabaseManager()