from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field # Field 用于给模型字段添加额外信息
from typing import Optional
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
        logger.error(f"应用启动时无法连接到Neo4j（错误将被忽略，应用将继续启动）: {e}") # 修改日志信息
        # 不再重新抛出异常或让应用在此处失败
    except Exception as e: # 可以捕获更广泛的异常，以防其他问题
        logger.error(f"应用启动时发生未知错误（将被忽略）: {e}")

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
# from .api.endpoints import graph_api as graph_endpoint # 新增导入 - 已移除，由 knowledge_endpoint 替代
from .api.endpoints import knowledge as knowledge_endpoint # Import the new knowledge router
from .api.v1.endpoints import ai as ai_endpoint # Import the new AI router
from .api.v1.endpoints import files as files_v1_endpoint # Import the new files router
from .api.v1.endpoints import pdf as pdf_endpoint # Import the new PDF router
from .api.v1.endpoints import entities as entities_endpoint # Import the new entities router
from .api.v1.endpoints import simple_qa as simple_qa_endpoint # Import the new Simple QA router

app.include_router(files_endpoint.router, prefix=f"{settings.API_PREFIX}/files", tags=["Files"]) # Legacy file operations
app.include_router(preprocessing_endpoint.router, prefix=f"{settings.API_PREFIX}/preprocessing", tags=["Preprocessing"])
# app.include_router(graph_endpoint.router, prefix=f"{settings.API_PREFIX}/graph", tags=["Graph"]) # 新增图数据库API路由 - 已移除
app.include_router(knowledge_endpoint.router, prefix=f"{settings.API_PREFIX}/knowledge", tags=["Knowledge"]) # Add knowledge router
app.include_router(ai_endpoint.router, prefix=f"{settings.API_PREFIX}/v1/ai", tags=["AI Service"]) # Add AI router with /v1
app.include_router(files_v1_endpoint.router, prefix=f"{settings.API_PREFIX}/v1/files", tags=["File Upload V1"]) # Add new File Upload router with /v1
app.include_router(pdf_endpoint.router, prefix=f"{settings.API_PREFIX}/v1/pdf", tags=["PDF Processing"]) # Add PDF Processing router
app.include_router(entities_endpoint.router, prefix=f"{settings.API_PREFIX}/v1/entities", tags=["Entity Recognition"]) # Add Entity Recognition router
app.include_router(simple_qa_endpoint.router, prefix=f"{settings.API_PREFIX}/v1/qa", tags=["Simple QA"]) # Add Simple QA router


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
    description: Optional[str] = Field(None, title="描述信息", max_length=300)
    price: float = Field(..., gt=0, description="价格必须大于0")
    tax: Optional[float] = None

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
