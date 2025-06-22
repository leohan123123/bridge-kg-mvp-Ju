# backend/app/services/__init__.py

# 这个文件使得 "services" 文件夹成为一个 Python 包。
# 服务层通常包含应用的业务逻辑。
# 你可以在这里组织你的服务类或函数。

# 例如，如果你有一个 user_service.py:
# from .user_service import UserService

# 目前为空，因为我们还没有具体的业务服务。

# __all__ 可以用来定义 `from .services import *` 时会导入哪些名称
# __all__ = ["UserService", "DXFParserService", "FileService", "DataPreprocessorService"]

from .dxf_parser import DXFParserService
from .file_service import FileService
from .data_preprocessor import DataPreprocessorService

pass
