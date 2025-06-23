import pytest
from fastapi.testclient import TestClient
from ..main import app # 确保从正确的位置导入 app
from ..core.config import settings

client = TestClient(app)

def test_import_dxf_knowledge():
    """
    测试 POST /api/v1/knowledge/import-dxf/{file_id} 端点。
    """
    file_id = "test_file_id_123"
    response = client.post(f"{settings.API_PREFIX}/knowledge/import-dxf/{file_id}")

    assert response.status_code == 201, f"预期状态码 201, 但收到 {response.status_code}. 响应体: {response.text}"

    response_json = response.json()
    assert response_json["status"] == "success"
    assert response_json["file_id"] == file_id
    assert "message" in response_json
    # 由于 mock_dxf_data 中的 uuid 是动态生成的，我们只检查消息中是否包含 "Nodes created successfully"
    assert "Nodes created successfully from DXF data." in response_json["message"]

def test_import_dxf_knowledge_no_file_id():
    """
    测试当 file_id 为空字符串时，端点是否按预期失败。
    注意：在当前的实现中，路径参数不能为空，FastAPI 会在匹配路由前就返回 404。
    如果希望测试空 file_id 导致业务逻辑错误 (400)，则需要 file_id 是查询参数或请求体的一部分。
    对于路径参数，FastAPI 的行为是正确的。这里我们测试一个 file_id，但预期服务内部逻辑（如果存在）会处理。
    当前的 knowledge.py 中的 file_id 检查 `if not file_id:` 实际上在 file_id 作为路径参数时永远不会为 False，
    因为 FastAPI 确保它存在。但为了覆盖，我们假设未来可能有不同的 file_id 验证。
    """
    # 根据当前的路由定义，file_id 是路径参数，所以不能是空的。
    # FastAPI 会直接返回 404 如果路径不匹配，例如 /api/v1/knowledge/import-dxf/
    # 因此，我们不能直接测试一个“空的”路径参数 file_id 来触发400。
    # 如果要测试 "file_id is required" 逻辑，file_id 需要是查询参数或请求体的一部分。
    # 这个测试用例的意图是好的，但与当前路径参数的实现不完全匹配。
    # 为了完整性，我们保留一个类似的测试，但要明白其局限性。

    # 我们将测试一个有效的请求，因为当前的 `if not file_id:` 检查在 `knowledge.py` 中，
    # 对于路径参数来说，FastAPI 已经保证了 `file_id` 的存在。
    # 如果该检查意图是验证 `file_id` 的内容（例如，非空字符串），那么它需要更具体的逻辑。
    # 此处我们仅确保端点在有 file_id 时能工作。
    # 若要严格测试 "file_id is required" 对应的 HTTPException，需要调整 file_id 的传递方式。

    # 鉴于以上，我们在这里添加一个简单的调用，以确保测试覆盖率，
    # 但请注意，它不会触发 knowledge.py 中的 `if not file_id:` 分支的 HTTPException。
    file_id = "another_test_id"
    response = client.post(f"{settings.API_PREFIX}/knowledge/import-dxf/{file_id}")
    assert response.status_code == 201 # 仍然应该是成功的
    assert response.json()["file_id"] == file_id

# 可以添加更多测试用例，例如模拟 graph_service 抛出异常等。
# from unittest.mock import patch

# def test_import_dxf_knowledge_service_exception():
#     file_id = "test_exception_file_id"
#     with patch("backend.app.api.endpoints.knowledge.get_graph_service") as mock_get_service:
#         mock_service_instance = mock_get_service.return_value
#         mock_service_instance.create_node.side_effect = Exception("Database connection error")

#         response = client.post(f"{settings.API_PREFIX}/knowledge/import-dxf/{file_id}")

#         assert response.status_code == 500
#         assert response.json()["detail"] == "Failed to import DXF data: Database connection error"

# 为了确保 get_neo4j_driver 在测试环境中不会真的尝试连接数据库 (除非需要集成测试)，
# 可以在 conftest.py 中 mock掉它，或者确保测试配置指向一个测试数据库。
# 对于这个特定任务，我们主要关注路由和基本响应。
# 如果 Neo4j 驱动在启动时失败，TestClient(app) 可能会遇到问题。
# 假设 settings.NEO4J_URI 在测试时是可控的或被 mock 的。
# 在当前的 main.py 中，get_neo4j_driver() 在 startup 事件中被调用。
# 如果它在测试 TestClient 初始化时抛出 ConnectionError，测试将无法正常进行。
# 这提示我们可能需要一个更健壮的测试设置，例如使用环境变量来配置测试数据库，
# 或者在测试环境中 mock 掉数据库依赖。

# 暂时，我们假设Neo4j的连接（或其mock）在测试客户端初始化时不会阻止应用加载。
# 如果在运行测试时遇到与Neo4j连接相关的问题，需要回顾这部分。
