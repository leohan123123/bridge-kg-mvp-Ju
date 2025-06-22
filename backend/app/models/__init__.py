# backend/app/models/__init__.py

# 这个文件使得 "models" 文件夹成为一个 Python 包。
# 你可以在这里导入各个模型文件中的主要模型类，
# 以便更容易地从其他地方导入它们，例如：
# from .user_model import User
# from .item_model import Item

# 目前为空，因为我们还没有具体的业务模型。
# 当你添加 Pydantic 模型 (例如 User.py, Product.py) 时，
# 可以在这里进行组织。

# 示例 (假设你创建了 item_model.py):
# from .item_model import ItemCreate, ItemResponse

# __all__ 可以用来定义 `from .models import *` 时会导入哪些名称
# __all__ = ["ItemCreate", "ItemResponse"]

pass
