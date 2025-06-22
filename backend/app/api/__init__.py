# backend/app/api/__init__.py

# 这个文件使得 "api" 文件夹成为一个 Python 包。
# API 路由模块通常放在这里。

# 你可以在 app/main.py 中像这样导入和包含路由：
# from .api import items_router, users_router # 假设你有 items_router.py 和 users_router.py
# app.include_router(items_router, prefix="/items", tags=["Items"])
# app.include_router(users_router, prefix="/users", tags=["Users"])

# 目前我们只有一个 health.py 路由。
# 在 app/main.py 中我们是这样导入的：
# from .api import health # (或者 from app.api import health)
# app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])

# 如果路由模块很多，可以在这里创建一个主路由器，然后由 app/main.py 包含这个主路由器。
# from fastapi import APIRouter
# from . import health # 导入同级目录下的 health.py 模块
# # from . import other_router_module # 导入其他路由模块
#
# api_router = APIRouter()
# api_router.include_router(health.router, tags=["Health"])
# # api_router.include_router(other_router_module.router, prefix="/items", tags=["Items"])

# 然后在 main.py 中:
# from app.api import api_router
# app.include_router(api_router, prefix=settings.API_PREFIX)

pass
