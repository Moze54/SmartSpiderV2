import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from smart_spider.main import app
from smart_spider.core.database import get_session
from smart_spider.models.database import Task, TaskResult, TaskStatus


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def test_tables(test_engine):
    """创建测试数据表"""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def test_session(test_engine, test_tables) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    AsyncSessionLocal = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_session):
    """创建测试客户端"""
    def override_get_session():
        return test_session

    app.dependency_overrides[get_session] = override_get_session

    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_task(test_session):
    """创建示例任务"""
    task = Task(
        task_id="test-task-123",
        name="测试任务",
        description="测试描述",
        urls=["https://example.com"],
        config={
            "name": "测试任务",
            "urls": ["https://example.com"],
            "parse_rules": {"title": "h1"}
        },
        status=TaskStatus.PENDING
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    return task


@pytest.fixture
async def sample_task_result(test_session, sample_task):
    """创建示例任务结果"""
    result = TaskResult(
        task_id=sample_task.task_id,
        data={"title": "测试标题", "content": "测试内容"},
        url="https://example.com",
        status_code=200,
        response_time=1.5
    )
    test_session.add(result)
    await test_session.commit()
    await test_session.refresh(result)
    return result