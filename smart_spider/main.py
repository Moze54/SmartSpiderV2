from fastapi import FastAPI
from smart_spider.api.routes import api_router
from smart_spider.core.config import settings
from smart_spider.core.logger import setup_logging

app = FastAPI(
    title="SmartSpider",
    description="一个接口驱动的智能爬虫系统",
    version="0.1.0"
)

# 初始化日志
setup_logging()

# 注册路由
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "SmartSpider 已启动"}