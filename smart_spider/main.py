from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from smart_spider.api.routes import router
from smart_spider.core.database import db_manager, init_db
from smart_spider.core.logger import logger

# 创建FastAPI应用
app = FastAPI(
    title="SmartSpider",
    description="一个高效的HTTP爬虫工具，通过RESTful API进行任务管理",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("SmartSpider 正在启动...")
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("SmartSpider 正在关闭...")
    try:
        from smart_spider.engine.crawler import crawler_engine
        await crawler_engine.cleanup()
        logger.info("爬虫任务清理完成")
    except Exception as e:
        logger.error(f"清理爬虫任务失败: {str(e)}")


# 注册路由
app.include_router(router)

# 注册增强版路由 (暂时注释掉，避免启动错误)
# from smart_spider.api.enhanced_routes import enhanced_router
# app.include_router(enhanced_router)


@app.get("/")
async def read_root():
    """根路径"""
    return {
        "message": "SmartSpider 爬虫工具已启动",
        "version": "1.0.0",
        "docs": "/docs",
        "api": "/api/v1"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "SmartSpider",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "smart_spider.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )