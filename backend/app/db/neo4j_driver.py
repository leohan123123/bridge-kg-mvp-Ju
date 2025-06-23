# backend/app/db/neo4j_driver.py
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import Neo4jError # Corrected import for Neo4jError
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

_driver: Driver = None

def get_neo4j_driver() -> Driver:
    """
    初始化并返回一个Neo4j驱动程序实例。
    如果驱动程序已初始化，则返回现有实例。
    包含基本的健康检查。
    """
    global _driver
    if _driver is None:
        try:
            logger.info(f"Initializing Neo4j driver for URI: {settings.NEO4J_URI}")
            _driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # 基本的健康检查：验证连接性
            with _driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("RETURN 1")
                if result.single()[0] == 1:
                    logger.info("Neo4j driver initialized and connection verified.")
                else:
                    logger.error("Neo4j connection verification failed.")
                    # 可以在这里抛出异常或采取其他错误处理措施
                    # 对于MVP，我们暂时只记录错误

        except Neo4jError as e:
            logger.error(f"Failed to initialize Neo4j driver or connect to Neo4j: {e}")
            # 在连接失败时，可以选择抛出异常，阻止应用启动，或者允许应用在没有数据库连接的情况下启动（取决于需求）
            # 例如: raise ConnectionError(f"Could not connect to Neo4j: {e}") from e
            _driver = None # 确保在失败时 _driver 仍然是 None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Neo4j driver initialization: {e}")
            _driver = None

    if _driver is None:
        # 如果在尝试初始化后驱动仍然是None，则抛出错误，表明应用无法在没有数据库的情况下运行。
        raise ConnectionError("Neo4j driver could not be initialized. Application cannot proceed without a database connection.")

    return _driver

def close_neo4j_driver():
    """
    关闭Neo4j驱动程序连接。
    """
    global _driver
    if _driver is not None:
        try:
            _driver.close()
            _driver = None
            logger.info("Neo4j driver closed.")
        except Neo4jError as e:
            logger.error(f"Error closing Neo4j driver: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during Neo4j driver closure: {e}")

def get_db_session():
    """
    提供一个依赖注入函数，用于在API路由中获取Neo4j会话。
    确保会话在使用后被关闭。
    """
    if _driver is None:
        # 尝试重新初始化，以防驱动程序因某种原因未被初始化（例如，在测试场景或延迟初始化中）
        # 在生产环境中，驱动程序应该在应用启动时已经初始化。
        logger.warning("Neo4j driver was None when get_db_session was called. Attempting to re-initialize.")
        try:
            get_neo4j_driver() # 这会尝试初始化 _driver
        except ConnectionError as e:
            logger.error(f"Failed to re-initialize Neo4j driver in get_db_session: {e}")
            raise # 重新抛出异常，因为没有数据库会话无法继续

    if _driver is None: # 再次检查，如果初始化失败
        raise ConnectionError("Cannot create Neo4j session: Driver is not available.")

    session = None
    try:
        session = _driver.session(database=settings.NEO4J_DATABASE)
        yield session
    except Neo4jError as e:
        logger.error(f"Error during Neo4j session or transaction: {e}")
        # 可以根据需要处理特定类型的 Neo4jError
        raise  # 重新抛出异常，让 FastAPI 的错误处理机制捕获
    finally:
        if session is not None and session.closed() is False:
            session.close()

# 示例：如何使用 get_db_session 在 FastAPI 路径操作函数中
# from fastapi import APIRouter, Depends, HTTPException
# from neo4j import Session as Neo4jSession # 使用类型别名以避免与 FastAPI 的 Session 冲突
#
# router = APIRouter()
#
# @router.get("/test-neo4j")
# async def test_neo4j_connection(db: Neo4jSession = Depends(get_db_session)):
#     try:
#         result = db.run("MATCH (n) RETURN count(n) AS node_count")
#         record = result.single()
#         node_count = record["node_count"] if record else 0
#         return {"message": "Successfully connected to Neo4j!", "node_count": node_count}
#     except Neo4jError as e:
#         logger.error(f"Neo4j query failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Neo4j query error: {e}")
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
#         raise HTTPException(status_code=500, detail="An unexpected server error.")

# 确保在 backend/app/db/__init__.py 中导入这些函数，使其易于访问
# 例如:
# from .neo4j_driver import get_neo4j_driver, close_neo4j_driver, get_db_session
# __all__ = ["get_neo4j_driver", "close_neo4j_driver", "get_db_session"]
