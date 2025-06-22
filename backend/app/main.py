from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field # Field 用于给模型字段添加额外信息
import logging
import os

from .core.config import settings # 导入配置
from .core.logging_config import setup_logging # 导入日志配置
from .api import health, files # 导入健康检查和文件处理路由

# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)

# 导入 Neo4j 驱动程序管理函数
from .db.neo4j_driver import get_neo4j_driver, close_neo4j_driver

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json", # API文档路径
    # docs_url=None, # 可以禁用默认的 /docs
    # redoc_url=None, # 可以禁用默认的 /redoc
)

# CORS 中间件配置
# 默认情况下，FastAPI的CORSMiddleware允许所有来源、所有方法、所有头。
# 为了安全起见，生产环境应该配置具体的origins。
if settings.ALLOWED_ORIGINS:
    origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
    logger.info(f"CORS 启用了特定源: {origins}")
else:
    origins = ["*"] # 开发环境下允许所有源
    logger.info("CORS 允许所有源 (开发模式)")


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 允许的源列表
    allow_credentials=True, # 是否支持cookies跨域
    allow_methods=["*"], # 允许所有方法 (GET, POST, PUT, DELETE 等)
    allow_headers=["*"], # 允许所有请求头
)

# 应用启动事件处理器
@app.on_event("startup")
async def startup_event():
    logger.info("应用启动中...")
    try:
        get_neo4j_driver() # 初始化Neo4j驱动并验证连接
        logger.info("Neo4j驱动已成功初始化。")
    except ConnectionError as e:
        logger.error(f"应用启动失败：无法连接到Neo4j。错误: {e}")
        # 根据应用的容错需求，这里可以选择退出应用或标记为不健康状态
        # 例如: raise RuntimeError(f"Failed to connect to Neo4j: {e}")
        # 对于当前设置，如果get_neo4j_driver抛出ConnectionError, FastAPI可能不会完全启动或会记录错误。

# 应用关闭事件处理器
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("应用关闭中...")
    close_neo4j_driver()
    logger.info("Neo4j驱动已关闭。")

# 包含API路由
app.include_router(health.router, prefix=f"{settings.API_PREFIX}/health", tags=["Health"]) # 更具体的prefix
# app.include_router(files.router, prefix=f"{settings.API_PREFIX}/files", tags=["Files"]) # 旧的文件处理API，将被endpoints下的替换

# 从 endpoints 导入路由
from .api.endpoints import files as files_endpoint
from .api.endpoints import preprocessing as preprocessing_endpoint
from .api.endpoints import graph_api as graph_endpoint # 新增导入
from .api.endpoints import knowledge as knowledge_endpoint # Import the new knowledge router

app.include_router(files_endpoint.router, prefix=f"{settings.API_PREFIX}/files", tags=["Files"])
app.include_router(preprocessing_endpoint.router, prefix=f"{settings.API_PREFIX}/preprocessing", tags=["Preprocessing"])
app.include_router(graph_endpoint.router, prefix=f"{settings.API_PREFIX}/graph", tags=["Graph"]) # 新增图数据库API路由
app.include_router(knowledge_endpoint.router, prefix=f"{settings.API_PREFIX}/knowledge", tags=["Knowledge"]) # Add knowledge router


# 根路径 (可选)
@app.get("/", tags=["Root"])
async def read_root() -> dict[str, str]:
    """
    根路径，返回欢迎信息。
    """
    logger.info("访问了根路径 /")
    return {"message": f"欢迎来到 {settings.PROJECT_NAME}!"}

# 示例：一个带Pydantic模型的POST请求
class Item(BaseModel):
    name: str
    description: str | None = Field(None, title="描述信息", max_length=300)
    price: float = Field(..., gt=0, description="价格必须大于0")
    tax: float | None = None

@app.post(f"{settings.API_PREFIX}/items/", response_model=Item, tags=["Items"])
async def create_item(item: Item) -> Item:
    """
    创建一个新的Item。
    使用Pydantic进行数据验证。
    """
    logger.info(f"创建Item: {item.name}")
    # 在这里可以添加将item存入数据库的逻辑
    # return item # FastAPI会自动将Pydantic模型转换为JSON响应
    # 假设我们给item增加一个id
    # created_item = item.copy(update={"id": 1}) # 只是示例
    return item

# 基础的错误处理 (FastAPI内置了对HTTPException的处理)
# 你可以添加自定义的异常处理器，例如：
# from fastapi import Request
# from fastapi.responses import JSONResponse
#
# @app.exception_handler(ValueError) # 捕获特定类型的异常
# async def value_error_exception_handler(request: Request, exc: ValueError):
#     logger.error(f"发生了值错误: {exc} (请求: {request.url.path})")
#     return JSONResponse(
#         status_code=400,
#         content={"message": f"捕获到值错误: {str(exc)}"},
#     )

if __name__ == "__main__":
    # 这个部分主要用于本地直接运行main.py进行调试，
    # 在Docker中通常由uvicorn或gunicorn命令启动。
    import uvicorn
    logger.info("启动开发服务器 (uvicorn app.main:app --reload)")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
