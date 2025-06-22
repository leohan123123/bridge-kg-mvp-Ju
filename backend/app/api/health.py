from fastapi import APIRouter
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class HealthResponse(BaseModel):
    status: str = "ok"

@router.get("/health", response_model=HealthResponse, summary="健康检查接口")
async def health_check() -> HealthResponse:
    """
    执行健康检查并返回服务状态。
    当服务正常运行时，返回 `{"status": "ok"}`。
    """
    logger.info("健康检查接口被调用, 服务状态: ok")
    return HealthResponse(status="ok")

# 可以在这里添加更复杂的健康检查逻辑，例如：
# - 检查数据库连接
# - 检查外部服务依赖
#
# from fastapi import Depends
# from ..core.db import get_db_session # 假设有数据库会话管理
#
# class DetailedHealthResponse(HealthResponse):
#     database_status: str
#
# @router.get("/health/detailed", response_model=DetailedHealthResponse, summary="详细健康检查")
# async def detailed_health_check(db = Depends(get_db_session)):
#     db_status = "ok"
#     try:
#         # 尝试执行一个简单的数据库查询
#         # await db.execute("SELECT 1") # 示例，具体取决于你的DB驱动
#         pass # 假设连接正常
#     except Exception as e:
#         logger.error(f"数据库健康检查失败: {e}")
#         db_status = "error"
#
#     overall_status = "ok" if db_status == "ok" else "error"
#     logger.info(f"详细健康检查: DB status: {db_status}, Overall: {overall_status}")
#     return DetailedHealthResponse(status=overall_status, database_status=db_status)
