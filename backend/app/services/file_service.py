# backend/app/services/file_service.py
"""
文件处理的核心服务逻辑
包括文件保存、删除、元数据管理等
"""
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from fastapi import UploadFile, HTTPException, status
from ..models.file_metadata import FileMetadataCreate, FileMetadataResponse
from ..core.config import settings

# 模块级常量，可以用作默认值
DEFAULT_UPLOAD_DIRECTORY = "backend/app/uploads"
DEFAULT_ALLOWED_EXTENSIONS = {".dxf", ".pdf", ".dwg"}
DEFAULT_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

class FileService:
    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_directory = upload_dir or getattr(settings, 'UPLOAD_DIRECTORY', DEFAULT_UPLOAD_DIRECTORY)
        self.allowed_extensions = getattr(settings, 'ALLOWED_EXTENSIONS', DEFAULT_ALLOWED_EXTENSIONS)
        self.max_file_size_bytes = getattr(settings, 'MAX_FILE_SIZE_BYTES', DEFAULT_MAX_FILE_SIZE_BYTES)

        # 确保上传目录存在
        os.makedirs(self.upload_directory, exist_ok=True)

        # 简化的内存中元数据存储 (用于演示)
        # 在多worker或需要持久性的情况下，应替换为数据库
        self._mock_metadata_db: List[FileMetadataResponse] = []

    async def save_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        验证、保存上传的文件，并创建元数据条目。
        这是 preprocessing.py 中期望的 save_file 方法的整合版本。
        """
        original_filename, stored_filename, file_size = await self._save_uploaded_file_to_disk(file)

        metadata_response = await self._create_file_metadata_entry(
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_size_bytes=file_size,
        )
        # preprocessing.py 期望返回一个包含 full_path, file_id, filename 的字典
        full_path = os.path.join(self.upload_directory, stored_filename)
        return {
            "file_id": metadata_response.id, # stored_filename is used as id
            "filename": original_filename,
            "full_path": full_path,
            "content_type": file.content_type, # FastAPI UploadFile has this
            "size_bytes": file_size,
            "metadata": metadata_response.model_dump() if hasattr(metadata_response, 'model_dump') else metadata_response.dict()
        }


    async def _save_uploaded_file_to_disk(self, file: UploadFile) -> Tuple[str, str, int]:
        """
        (内部方法) 验证并保存单个上传的文件到磁盘。
        """
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1].lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件类型 '{file_extension}' 不被允许。只接受 {', '.join(self.allowed_extensions)} 文件。"
            )

        contents = await file.read()
        file_size = len(contents)
        await file.seek(0)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件 '{original_filename}' 为空，不允许上传空文件。"
            )

        if file_size > self.max_file_size_bytes:
            max_size_mb = self.max_file_size_bytes / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件 '{original_filename}' 大小 ({file_size / (1024 * 1024):.2f}MB) 超过 {max_size_mb:.0f}MB 限制。"
            )

        stored_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(self.upload_directory, stored_filename)

        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except IOError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"无法保存文件 '{original_filename}' 到服务器。错误: {e}"
            )
        finally:
            await file.close()

        return original_filename, stored_filename, file_size

    async def _create_file_metadata_entry(
        self,
        original_filename: str,
        stored_filename: str,
        file_size_bytes: int,
        file_type: Optional[str] = None,
    ) -> FileMetadataResponse:
        """
        (内部方法) 创建并存储文件元数据记录。
        """
        if not file_type:
            file_type = os.path.splitext(original_filename)[1].lower()

        metadata_create = FileMetadataCreate(
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
        )

        metadata_response = FileMetadataResponse(
            id=stored_filename, # Use stored_filename as ID
            uploaded_at=datetime.utcnow(),
            file_url=f"/files/download/{stored_filename}", # Example URL
            **(metadata_create.model_dump() if hasattr(metadata_create, 'model_dump') else metadata_create.dict())
        )
        self._mock_metadata_db.append(metadata_response)
        return metadata_response

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        根据文件ID获取单个文件的元数据 (preprocessing.py 期望的格式)。
        注意：原先的 get_file_metadata_by_id 返回 FileMetadataResponse。
        preprocessing.py 中的 file_service.get_file_metadata(file_id) 期望返回一个字典
        包含 'full_path' 和 'filename'。
        """
        for metadata_model in self._mock_metadata_db:
            if metadata_model.id == file_id: # file_id is stored_filename
                full_path = os.path.join(self.upload_directory, metadata_model.stored_filename)
                return {
                    "file_id": metadata_model.id,
                    "filename": metadata_model.original_filename,
                    "full_path": full_path,
                    "content_type": metadata_model.file_type, # Assuming file_type is content_type like
                    "size_bytes": metadata_model.file_size_bytes,
                    "metadata_model": metadata_model # Keep original model if needed elsewhere
                }
        return None

    async def get_all_file_metadata_models(self) -> List[FileMetadataResponse]:
        """
        获取所有文件的元数据模型列表。
        """
        return list(self._mock_metadata_db)


    async def get_file_metadata_model_by_id(self, file_id: str) -> Optional[FileMetadataResponse]:
        """
        根据文件ID获取单个文件的元数据模型。
        """
        for metadata in self._mock_metadata_db:
            if metadata.id == file_id:
                return metadata
        return None

    async def delete_file_and_metadata(self, file_id: str) -> bool:
        """
        根据文件ID（存储文件名）删除文件及其元数据。
        """
        metadata_to_delete = None
        for metadata_model in self._mock_metadata_db:
            if metadata_model.id == file_id:
                metadata_to_delete = metadata_model
                break

        if not metadata_to_delete:
            return False

        file_path = os.path.join(self.upload_directory, metadata_to_delete.stored_filename)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            print(f"警告: 无法删除物理文件 '{file_path}': {e}")
            # Decide if this should be a critical failure or just a warning

        self._mock_metadata_db = [m for m in self._mock_metadata_db if m.id != file_id]
        return True

    async def get_physical_file_path(self, stored_filename: str) -> Optional[str]:
        """
        获取存储文件的物理路径。
        """
        path = os.path.join(self.upload_directory, stored_filename)
        if os.path.exists(path) and os.path.isfile(path):
            return path
        return None

# Example of how FileService might be instantiated and used by preprocessing.py:
# file_service_instance = FileService(upload_dir=settings.UPLOAD_DIRECTORY)
# metadata = await file_service_instance.save_file(uploaded_file_object)
# file_info = file_service_instance.get_file_metadata(some_file_id)
# if file_info:
#     path = file_info["full_path"]
#     name = file_info["filename"]
