import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from smart_spider.main import app


class TestAPI:
    """测试API接口"""

    def setup_method(self):
        """设置测试环境"""
        self.client = TestClient(app)

    def test_health_check(self):
        """测试健康检查接口"""
        response = self.client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_create_task(self):
        """测试创建任务接口"""
        task_data = {
            "name": "测试任务",
            "description": "测试描述",
            "urls": ["https://example.com"],
            "parse_rules": {"title": "h1"}
        }
        response = self.client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 200
        assert response.json()["name"] == "测试任务"

    def test_create_task_invalid_url(self):
        """测试创建任务时提供无效URL"""
        task_data = {
            "name": "测试任务",
            "description": "测试描述",
            "urls": ["invalid-url"],
            "parse_rules": {"title": "h1"}
        }
        response = self.client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 422  # 验证错误

    def test_get_tasks(self):
        """测试获取任务列表接口"""
        response = self.client.get("/api/v1/tasks")
        assert response.status_code == 200
        assert isinstance(response.json()["items"], list)

    def test_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        response = self.client.get("/api/v1/tasks/nonexistent-task-id")
        assert response.status_code == 404

    def test_start_nonexistent_task(self):
        """测试启动不存在的任务"""
        response = self.client.post("/api/v1/tasks/nonexistent-task-id/start")
        assert response.status_code == 404

    def test_stop_nonexistent_task(self):
        """测试停止不存在的任务"""
        response = self.client.post("/api/v1/tasks/nonexistent-task-id/stop")
        assert response.status_code == 404

    def test_delete_nonexistent_task(self):
        """测试删除不存在的任务"""
        response = self.client.delete("/api/v1/tasks/nonexistent-task-id")
        assert response.status_code == 404

    def test_get_task_results(self):
        """测试获取任务结果接口"""
        # 先创建一个任务
        task_data = {
            "name": "测试任务",
            "urls": ["https://example.com"],
            "parse_rules": {"title": "h1"}
        }
        create_response = self.client.post("/api/v1/tasks", json=task_data)
        task_id = create_response.json()["task_id"]

        # 获取任务结果
        response = self.client.get(f"/api/v1/tasks/{task_id}/results")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_quick_start_task(self):
        """测试快速启动任务接口"""
        quick_data = {
            "url": "https://example.com",
            "parse_rules": {"title": "h1"}
        }
        response = self.client.post("/api/v1/tasks/quick-start", json=quick_data)
        assert response.status_code == 200
        assert response.json()["name"] == "快速任务-https://example.com"

    def test_task_status_filtering(self):
        """测试任务状态过滤"""
        # 测试按状态过滤
        response = self.client.get("/api/v1/tasks?status=PENDING")
        assert response.status_code == 200
        assert isinstance(response.json()["items"], list)

    def test_pagination(self):
        """测试分页功能"""
        response = self.client.get("/api/v1/tasks?limit=5&offset=0")
        assert response.status_code == 200
        assert response.json()["total"] >= 0
        assert len(response.json()["items"]) <= 5

    def test_invalid_json_payload(self):
        """测试无效的JSON负载"""
        response = self.client.post(
            "/api/v1/tasks",
            json={"invalid": "payload"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_async_client(self):
        """测试异步客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/api/v1/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"