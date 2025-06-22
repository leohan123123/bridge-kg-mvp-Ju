# backend/app/services/file_service.py
"""
文件处理的核心服务逻辑
包括文件保存、删除、元数据管理等
"""
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import UploadFile, HTTPException, status
from ..models.file_metadata import FileMetadataCreate, FileMetadataResponse # 使用相对导入
from ..core.config import settings # 假设配置中会有 UPLOAD_DIRECTORY

# UPLOAD_DIRECTORY = "backend/app/uploads" # 暂时硬编码，理想情况下从配置读取
# 尝试从 settings 获取，如果 settings 中没有定义，则使用默认值
UPLOAD_DIRECTORY = getattr(settings, 'UPLOAD_DIRECTORY', "backend/app/uploads")
ALLOWED_EXTENSIONS = getattr(settings, 'ALLOWED_EXTENSIONS', {".dxf", ".pdf", ".dwg"})
MAX_FILE_SIZE_BYTES = getattr(settings, 'MAX_FILE_SIZE_BYTES', 50 * 1024 * 1024) # 50MB

# 确保上传目录存在
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# 简化的内存中元数据存储 (用于演示，实际应用中应使用数据库)
# 注意：这在多worker环境下会有问题，数据不会共享且重启会丢失
_mock_metadata_db: List[FileMetadataResponse] = []


async def save_uploaded_file(file: UploadFile) -> Tuple[str, str, int]:
    """
    验证并保存单个上传的文件。

    Args:
        file: FastAPI的UploadFile对象.

    Returns:
        Tuple[str, str, int]: 包含原始文件名, 存储的文件名和文件大小 (字节) 的元组.

    Raises:
        HTTPException: 如果文件类型或大小无效.
    """
    # 1. 文件类型验证
    original_filename = file.filename
    file_extension = os.path.splitext(original_filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件类型 '{file_extension}' 不被允许。只接受 {', '.join(ALLOWED_EXTENSIONS)} 文件。"
        )

    # 2. 文件大小验证 (读取文件内容来确定实际大小)
    # 使用 SpooledTemporaryFile (FastAPI/Starlette 默认行为) 时，
    # file.file 是一个类文件对象。我们需要读取它来获取内容和大小。
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0) # 重置文件指针，以便后续可能的再次读取或保存

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件 '{original_filename}' 为空，不允许上传空文件。"
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        max_size_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件 '{original_filename}' 大小 ({file_size / (1024 * 1024):.2f}MB) 超过 {max_size_mb:.0f}MB 限制。"
        )

    # 3. 生成唯一文件名 (保留原始扩展名)
    stored_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, stored_filename)

    # 4. 保存文件到磁盘
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f) # 使用 shutil.copyfileobj 更高效
    except IOError as e:
        # server_error_logging(e) # 假设有日志记录
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"无法保存文件 '{original_filename}' 到服务器。错误: {e}"
        )
    finally:
        await file.close() # 确保关闭文件

    return original_filename, stored_filename, file_size


async def create_file_metadata_entry(
    original_filename: str,
    stored_filename: str,
    file_size_bytes: int,
    file_type: Optional[str] = None,
    # uploader_id: Optional[str] = None # 如果需要记录上传者
) -> FileMetadataResponse:
    """
    创建并存储文件元数据记录。
    在实际应用中，这里会与数据库交互。
    """
    if not file_type:
        file_type = os.path.splitext(original_filename)[1].lower()

    metadata_create = FileMetadataCreate(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        # uploader_id=uploader_id,
    )

    # 模拟数据库存储和ID生成
    # 在真实场景中，数据库会生成 ID，uploaded_at 会是数据库的 `default=now()`
    metadata_response = FileMetadataResponse(
        id=stored_filename, # 使用存储文件名作为唯一ID (简化)
        uploaded_at=datetime.utcnow(), # 生成上传时间
        file_url=f"/files/download/{stored_filename}", # 构造一个假设的下载URL
        # Pydantic v2 使用 model_dump()，Pydantic v1 使用 dict()
        **metadata_create.model_dump() if hasattr(metadata_create, 'model_dump') else metadata_create.dict()
    )
    _mock_metadata_db.append(metadata_response) # 添加到模拟数据库
    return metadata_response


async def get_all_file_metadata() -> List[FileMetadataResponse]:
    """
    获取所有文件的元数据列表。
    在实际应用中，这里会从数据库查询。
    """
    # 返回副本以防外部修改
    return list(_mock_metadata_db)


async def get_file_metadata_by_id(file_id: str) -> Optional[FileMetadataResponse]:
    """
    根据文件ID（在此简化示例中为存储文件名）获取单个文件的元数据。
    """
    for metadata in _mock_metadata_db:
        if metadata.id == file_id:
            return metadata
    return None


async def delete_file_and_metadata(file_id: str) -> bool:
    """
    根据文件ID（存储文件名）删除文件及其元数据。
    """
    global _mock_metadata_db
    metadata_to_delete = None
    for metadata in _mock_metadata_db:
        if metadata.id == file_id: # file_id 在这里是 stored_filename
            metadata_to_delete = metadata
            break

    if not metadata_to_delete:
        return False # 文件元数据未找到

    file_path = os.path.join(UPLOAD_DIRECTORY, metadata_to_delete.stored_filename)

    # 1. 删除物理文件
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            # 文件已不存在，但元数据还在，也算部分成功（清除了元数据）
            pass
    except OSError as e:
        # server_error_logging(e) # 假设有日志记录
        # 如果删除文件失败，可能需要决定是否也回滚元数据删除或标记为孤立
        # 为简单起见，我们继续删除元数据
        print(f"警告: 无法删除物理文件 '{file_path}': {e}")
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"无法删除物理文件 '{metadata_to_delete.original_filename}'.")


    # 2. 删除元数据条目
    _mock_metadata_db = [m for m in _mock_metadata_db if m.id != file_id]

    # 病毒扫描占位符
    # print(f"TODO: 对文件 {metadata_to_delete.original_filename} 执行病毒扫描 (模拟)")

    return True


# 可以在此添加更多服务函数，例如：
# - 更新文件元数据
# - 按条件搜索/筛选文件
# - 获取文件的物理路径供下载等
async def get_physical_file_path(stored_filename: str) -> Optional[str]:
    """
    获取存储文件的物理路径。
    """
    path = os.path.join(UPLOAD_DIRECTORY, stored_filename)
    if os.path.exists(path) and os.path.isfile(path):
        return path
    return None
