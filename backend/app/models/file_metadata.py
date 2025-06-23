# backend/app/models/file_metadata.py
"""
文件元数据相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class FileMetadataBase(BaseModel):
    """
    文件元数据的基础模型
    """
    original_filename: str = Field(..., description="原始文件名")
    stored_filename: str = Field(..., description="存储在服务器上的唯一文件名")
    file_type: Optional[str] = Field(None, description="文件MIME类型或扩展名")
    file_size_bytes: int = Field(..., description="文件大小（字节）")
    # 可以在这里添加更多元数据字段，例如：
    # uploader_id: Optional[str] = Field(None, description="上传用户ID")
    # description: Optional[str] = Field(None, description="文件描述")
    # tags: List[str] = Field(default_factory=list, description="文件标签")

class FileMetadataCreate(FileMetadataBase):
    """
    创建文件元数据时使用的模型
    上传时间会自动生成，不需要创建时提供
    """
    pass

class FileMetadataResponse(FileMetadataBase):
    """
    从API响应中返回文件元数据时使用的模型
    """
    id: str = Field(..., description="文件元数据的唯一ID (例如，数据库主键或存储文件名)") # 根据实际存储方式调整
    uploaded_at: datetime = Field(..., description="文件上传时间")
    file_url: Optional[str] = Field(None, description="文件的可访问URL (如果适用)")

    model_config = {
        "from_attributes": True  # Pydantic V2 equivalent of orm_mode = True
    }


class PaginatedFileMetadataResponse(BaseModel):
    """
    分页获取文件元数据列表的响应模型
    """
    total: int = Field(..., description="文件总数")
    items: list[FileMetadataResponse] = Field(..., description="当前页的文件元数据列表")
    page: Optional[int] = Field(None, description="当前页码")
    size: Optional[int] = Field(None, description="每页大小")

# 示例：如果文件元数据存储在数据库中，这可能是一个 ORM 模型的简化表示
# class FileMetadataInDB(FileMetadataResponse):
#     # 可能包含数据库特有的字段，如哈希值等
#     content_hash: Optional[str] = None
#     pass

# 更多模型可以根据需要添加，例如用于更新元数据的模型等
# class FileMetadataUpdate(BaseModel):
#     description: Optional[str] = None
#     tags: Optional[List[str]] = None
#     original_filename: Optional[str] = None
