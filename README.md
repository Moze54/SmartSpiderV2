# SmartSpider - 智能网络爬虫系统

一个功能强大的异步网络爬虫框架，提供完整的API接口和命令行工具，支持任务调度、代理管理、Cookie管理、数据导出等高级功能。

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- Windows/Linux/MacOS

### 2. 安装依赖
```bash
# 安装依赖
pip install -r requirements.txt
```

### 3. 启动系统
```bash
# 启动服务器
python -m smart_spider server

# 或者指定端口和主机
python -m smart_spider server --port 8080 --host 127.0.0.1
```

### 4. 访问API文档
- Swagger文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## 📋 CLI命令使用指南

### 基础命令
```bash
# 查看帮助
python -m smart_spider --help

# 系统初始化（创建必要的目录）
python -m smart_spider init

# 启动服务器
python -m smart_spider server

# 运行健康检查
python -m smart_spider health

# 清理旧数据
python -m smart_spider cleanup

# 检查代理状态
python -m smart_spider proxy-check

# 验证Cookie
python -m smart_spider cookie-check

# 系统优化
python -m smart_spider optimize
```

### 服务器参数
```bash
python -m smart_spider server --help

# 参数说明：
# --host: 服务器主机地址 (默认: 0.0.0.0)
# --port: 服务器端口 (默认: 8000)
# --reload: 开发模式自动重载
```

## 🔧 API接口使用

### 1. 健康检查
```bash
# 检查系统状态
curl http://localhost:8000/api/v1/health

# 响应示例
{"status":"healthy","service":"SmartSpider"}
```

### 2. 任务管理

#### 创建任务
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试爬虫任务",
    "url": "https://example.com",
    "spider_type": "general",
    "config": {
      "max_pages": 10,
      "delay": 1.0,
      "use_proxy": false
    }
  }'
```

#### 获取任务列表
```bash
# 获取所有任务
curl http://localhost:8000/api/v1/tasks

# 分页获取
curl "http://localhost:8000/api/v1/tasks?page=1&size=20"

# 按状态筛选
curl "http://localhost:8000/api/v1/tasks?status=running"
```

#### 获取单个任务
```bash
curl http://localhost:8000/api/v1/tasks/{task_id}
```

#### 更新任务
```bash
curl -X PUT "http://localhost:8000/api/v1/tasks/{task_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "paused",
    "config": {
      "max_pages": 20
    }
  }'
```

#### 删除任务
```bash
curl -X DELETE "http://localhost:8000/api/v1/tasks/{task_id}"
```

#### 启动/停止任务
```bash
# 启动任务
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/start"

# 停止任务
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/stop"

# 暂停任务
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/pause"

# 恢复任务
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/resume"
```

### 3. 任务结果管理

#### 获取任务结果
```bash
# 获取任务结果
curl "http://localhost:8000/api/v1/tasks/{task_id}/results"

# 分页获取结果
curl "http://localhost:8000/api/v1/tasks/{task_id}/results?page=1&size=50"
```

#### 导出任务结果
```bash
# 导出为JSON格式
curl "http://localhost:8000/api/v1/tasks/{task_id}/export?format=json"

# 导出为CSV格式
curl "http://localhost:8000/api/v1/tasks/{task_id}/export?format=csv"

# 导出为Excel格式
curl "http://localhost:8000/api/v1/tasks/{task_id}/export?format=excel"
```

### 4. 代理管理

#### 添加代理
```bash
curl -X POST "http://localhost:8000/api/v1/proxies" \
  -H "Content-Type: application/json" \
  -d '{
    "proxy_url": "http://proxy.example.com:8080",
    "proxy_type": "http"
  }'
```

#### 获取代理列表
```bash
curl http://localhost:8000/api/v1/proxies
```

#### 检查代理健康状态
```bash
curl -X POST "http://localhost:8000/api/v1/proxies/check"
```

#### 删除代理
```bash
curl -X DELETE "http://localhost:8000/api/v1/proxies/{proxy_id}"
```

### 5. Cookie管理

#### 保存Cookie
```bash
curl -X POST "http://localhost:8000/api/v1/cookies" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "cookies": {
      "session_id": "abc123",
      "user_token": "xyz789"
    }
  }'
```

#### 获取Cookie
```bash
# 获取指定域名的Cookie
curl "http://localhost:8000/api/v1/cookies/example.com"
```

#### 清理过期Cookie
```bash
curl -X DELETE "http://localhost:8000/api/v1/cookies/expired"
```

### 6. 数据导出

#### 获取导出统计
```bash
curl http://localhost:8000/api/v1/export/stats
```

#### 导出数据
```bash
# 导出所有任务数据
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": ["task1", "task2"],
    "formats": ["json", "csv"]
  }'
```

### 7. 系统管理

#### 获取系统统计
```bash
curl http://localhost:8000/api/v1/stats
```

#### 获取系统配置
```bash
curl http://localhost:8000/api/v1/config
```

## 📊 配置说明

### 数据库配置
项目默认使用SQLite数据库，无需额外配置。数据库文件会自动创建在项目根目录下：`smartspider.db`

如果需要使用其他数据库，请修改 `smart_spider/config/simple_config.py` 文件：

```python
# MySQL配置示例
@property
def url(self) -> str:
    return "mysql+aiomysql://username:password@localhost:3306/smartspider"

# PostgreSQL配置示例
@property
def url(self) -> str:
    return "postgresql+asyncpg://username:password@localhost:5432/smartspider"
```

### 日志配置
日志文件会自动保存在 `logs/` 目录下，包括：
- `smartspider.log` - 主日志文件
- `crawler.log` - 爬虫日志文件
- `error.log` - 错误日志文件

### 存储配置
- **输出目录**: `output/` - 存放导出的数据文件
- **存储目录**: `storage/` - 存放任务配置、结果和日志
- **Cookie目录**: `cookies/` - 存放Cookie文件
- **上传目录**: `uploads/` - 存放上传的文件

## 🎯 高级功能

### 1. 任务调度
支持三种类型的定时任务：
- **Cron任务**: 基于cron表达式的定时任务
- **间隔任务**: 每隔固定时间执行的任务
- **一次性任务**: 在指定时间执行一次的任务

### 2. 代理管理
- 自动检测代理可用性
- 支持HTTP/HTTPS/SOCKS代理
- 代理池管理和轮换
- 代理健康状态监控

### 3. Cookie管理
- 自动保存和加载Cookie
- Cookie过期检测和清理
- 支持浏览器Cookie导入
- Cookie轮换策略

### 4. 数据导出
支持多种数据导出格式：
- JSON格式
- CSV格式
- Excel格式
- 自定义格式

### 5. 重试机制
- 智能重试策略
- 指数退避算法
- 熔断器保护
- 自适应重试调整

## 🔍 监控和调试

### 查看日志
```bash
# 实时查看日志
tail -f logs/smartspider.log

# 查看错误日志
tail -f logs/error.log

# 查看爬虫日志
tail -f logs/crawler.log
```

### 性能监控
- 系统会自动记录各项性能指标
- 可以通过API获取系统统计信息
- 支持Prometheus指标导出

## 🚨 常见问题和解决方案

### 1. 端口被占用
```bash
# 更换端口启动
python -m smart_spider server --port 8080
```

### 2. 权限问题
确保当前用户对以下目录有读写权限：
- `logs/`
- `output/`
- `storage/`
- `cookies/`
- `uploads/`

### 3. 数据库连接失败
如果使用外部数据库，请检查：
- 数据库服务是否启动
- 连接参数是否正确
- 网络连接是否正常

### 4. 内存使用过高
- 调整并发请求数量
- 定期清理旧数据
- 优化爬虫配置参数

## 🔧 开发指南

### 添加新的爬虫类型
1. 在 `smart_spider/spiders/` 目录下创建新的爬虫类
2. 继承基础爬虫类并实现必要的方法
3. 在配置中注册新的爬虫类型

### 自定义数据导出格式
1. 在 `smart_spider/storage/data_exporter.py` 中添加新的导出方法
2. 在 `export_to_format` 方法中添加对应的格式处理

### 扩展API接口
1. 在 `smart_spider/api/routes.py` 中添加新的路由
2. 使用FastAPI的装饰器定义接口
3. 添加相应的请求/响应模型

## 📞 技术支持

如果遇到问题，请：
1. 查看日志文件获取错误信息
2. 使用健康检查命令诊断系统状态
3. 检查配置文件是否正确
4. 确保所有依赖项已正确安装

---

**注意**: 本项目为后端API服务，不提供前端界面。所有操作都通过API或CLI命令完成。