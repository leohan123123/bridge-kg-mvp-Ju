# backend/app/core/__init__.py

# 这个文件使得 "core" 文件夹成为一个 Python 包。
# 核心配置、全局依赖项等通常放在这里。

# 例如，我们已经在这里放置了:
# - config.py (应用配置)
# - logging_config.py (日志配置)

# 你可能还会添加:
# - database.py (数据库连接和会话管理)
# - security.py (认证和授权相关的函数)
# - dependencies.py (通用的 FastAPI 依赖项)

# 从这个包中导入 settings 对象，方便其他模块使用：
from .config import settings

__all__ = ["settings"]
