# SmartSpider - 智能爬虫工具

SmartSpider 是一个基于 FastAPI 的高性能异步爬虫工具，专为开发者设计，通过简单的 REST API 接口即可实现强大的网页爬取功能。

## 🚀 项目特性

- **异步高性能**: 基于 asyncio 和 aiohttp 实现高并发爬取
- **RESTful API**: 提供完整的 HTTP API 接口，易于集成
- **灵活配置**: 支持 CSS 选择器和 XPath 表达式进行数据提取
- **任务管理**: 支持任务的创建、启动、停止、删除等全生命周期管理
- **错误处理**: 完善的异常处理机制，提供详细的错误信息
- **数据库支持**: 使用 MySQL 存储任务和结果数据
- **测试覆盖**: 包含完整的单元测试和集成测试

## 📋 功能清单

### 核心功能
- [x] 网页内容爬取
- [x] 数据解析提取
- [x] 任务生命周期管理
- [x] 配置管理
- [x] 错误处理与重试机制
- [x] 结果存储与查询

### API 接口
- [x] 任务创建与管理
- [x] 任务状态查询
- [x] 爬取结果获取
- [x] 健康检查
- [x] 快速启动任务

### 技术特性
- [x] 异步非阻塞 I/O
- [x] 并发控制
- [x] 代理支持
- [x] 速率限制
- [x] 超时处理
- [x] 日志记录

## 🛠️ 技术栈

- **后端框架**: FastAPI (基于 Starlette 和 Pydantic)
- **异步 HTTP**: aiohttp
- **数据库**: MySQL + SQLAlchemy (异步支持)
- **HTML 解析**: BeautifulSoup4 + lxml
- **配置管理**: Pydantic Settings
- **测试框架**: pytest + httpx
- **部署**: uvicorn

## 📦 安装与配置

### 环境要求

- Python 3.8+
- MySQL 5.7+

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/smartspider.git
   cd smartspider
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置数据库连接等信息
   ```

5. **初始化数据库**
   ```bash
   python init_db.py
   ```

6. **启动服务**
   ```bash
   python run.py
   ```

## ⚙️ 配置说明

### 数据库配置

在 `.env` 文件中配置数据库连接：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=smartspider
```

### 应用配置

应用配置位于 `smart_spider/config/crawler_config.py` 中，支持以下配置项：

- **并发控制**: max_concurrent_requests, request_delay
- **超时设置**: timeout, retry_times, retry_delay
- **用户代理**: user_agent
- **代理设置**: proxies, proxy_rotation
- **数据提取**: selector_type (css/xpath), parse_rules

## 🎯 快速开始

### 1. 创建爬虫任务

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "示例任务",
    "description": "爬取示例网站",
    "urls": ["https://example.com"],
    "parse_rules": {
      "title": "h1",
      "links": "a"
    },
    "selector_type": "css"
  }'
```

### 2. 启动任务

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/start"
```

### 3. 查询任务状态

```bash
curl "http://localhost:8000/api/v1/tasks/{task_id}/status"
```

### 4. 获取爬取结果

```bash
curl "http://localhost:8000/api/v1/tasks/{task_id}/results"
```

### 5. 快速启动（一步完成）

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/quick-start" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "parse_rules": {"title": "h1", "content": ".content"}
  }'
```

## 📖 API 文档

### 任务管理接口

#### 创建任务
```http
POST /api/v1/tasks
```

**请求体示例：**
```json
{
  "name": "任务名称",
  "description": "任务描述",
  "urls": ["https://example.com"],
  "parse_rules": {
    "title": "h1",
    "content": ".content"
  },
  "max_concurrent_requests": 5,
  "request_delay": 1.0,
  "timeout": 30,
  "retry_times": 3,
  "selector_type": "css"
}
```

#### 任务操作
- `POST /api/v1/tasks/{task_id}/start` - 启动任务
- `POST /api/v1/tasks/{task_id}/stop` - 停止任务
- `DELETE /api/v1/tasks/{task_id}` - 删除任务
- `GET /api/v1/tasks/{task_id}` - 获取任务详情
- `GET /api/v1/tasks/{task_id}/results` - 获取爬取结果
- `GET /api/v1/tasks/{task_id}/status` - 获取任务状态

#### 任务列表
```http
GET /api/v1/tasks?status=PENDING&limit=10&offset=0
```

## 🧪 测试

项目包含完整的测试套件：

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定测试
```bash
pytest tests/test_api.py -v
pytest tests/test_crawler_config.py -v
pytest tests/test_downloader.py -v
pytest tests/test_parser.py -v
```

### 生成测试报告
```bash
pytest tests/ --cov=smart_spider --cov-report=html
```

## 📊 项目结构

```
smartspider/
├── smart_spider/               # 主项目目录
│   ├── api/                   # API 接口
│   │   ├── routes.py         # 路由定义
│   │   └── schemas.py        # 数据模型
│   ├── config/               # 配置管理
│   │   └── crawler_config.py
│   ├── core/                 # 核心组件
│   │   ├── database.py       # 数据库连接
│   │   ├── exceptions.py     # 异常定义
│   │   └── logger.py         # 日志配置
│   ├── engine/               # 爬虫引擎
│   │   ├── crawler.py        # 主爬虫引擎
│   │   ├── downloader.py     # 下载器
│   │   └── parser.py         # 解析器
│   ├── models/               # 数据模型
│   │   └── database.py       # 数据库模型
│   ├── services/             # 业务服务
│   │   └── task_service.py   # 任务服务
│   └── main.py               # FastAPI 应用
├── tests/                    # 测试目录
│   ├── conftest.py          # 测试配置
│   ├── test_api.py          # API 测试
│   ├── test_crawler_config.py
│   ├── test_downloader.py
│   └── test_parser.py
├── logs/                     # 日志目录
├── output/                   # 输出目录
├── init_db.py               # 数据库初始化脚本
├── run.py                   # 启动脚本
├── requirements.txt         # 依赖列表
└── README.md               # 项目文档
```

## 🔧 高级用法

### 自定义选择器

支持 CSS 选择器和 XPath 表达式：

```json
{
  "parse_rules": {
    "title": "h1.title",
    "price": ".price::text",
    "description": "//div[@class='description']/p/text()",
    "links": "a[href]"
  },
  "selector_type": "css"
}
```

### 代理配置

```json
{
  "crawler": {
    "proxies": [
      "http://proxy1:8080",
      "http://proxy2:8080"
    ],
    "proxy_rotation": true
  }
}
```

### 速率限制

```json
{
  "crawler": {
    "max_concurrent_requests": 5,
    "request_delay": 1.0,
    "timeout": 30,
    "retry_times": 3
  }
}
```

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 MySQL 服务是否运行
   - 确认数据库用户权限
   - 验证连接参数配置

2. **爬取超时**
   - 增加 timeout 配置值
   - 检查网络连接
   - 启用代理或 VPN

3. **内存不足**
   - 减少 max_concurrent_requests
   - 分批处理大量 URL
   - 定期清理任务结果

### 日志查看

日志文件位于 `logs/` 目录：
- `app.log` - 应用日志
- `crawler.log` - 爬虫引擎日志
- `error.log` - 错误日志

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**SmartSpider** - 让数据爬取变得简单而强大！