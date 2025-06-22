# backend/app/api/files.py
"""
文件处理相关的API路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Response
from fastapi.responses import FileResponse
from typing import List, Optional
import os

from ..services import file_service # 使用相对导入
from ..models.file_metadata import FileMetadataResponse, PaginatedFileMetadataResponse # 使用相对导入
from ..core.config import settings # 假设配置中会有 UPLOAD_DIRECTORY

router = APIRouter()

# 从 service 获取配置或使用默认值 (如果 service 中有定义的话)
# 否则，直接在这里定义或从 settings 获取
UPLOAD_DIRECTORY = getattr(settings, 'UPLOAD_DIRECTORY', "backend/app/uploads")


@router.post("/upload", summary="上传单个或多个文件", response_model=List[FileMetadataResponse])
async def upload_files_endpoint(files: List[UploadFile] = File(...)):
    """
    处理文件上传的API端点。
    支持单个或多个文件上传。
    会进行文件类型和大小验证 (由 service 层处理)。
    成功上传后返回每个文件的元数据。
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有提供任何文件进行上传。"
        )

    uploaded_files_metadata: List[FileMetadataResponse] = []

    for file in files:
        try:
            # 1. 保存文件本身 (service负责验证类型、大小和保存)
            original_filename, stored_filename, file_size_bytes = await file_service.save_uploaded_file(file)

            # 2. 创建并存储文件元数据 (service负责)
            # 假设 uploader_id 暂时不处理或为 None
            metadata = await file_service.create_file_metadata_entry(
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size_bytes=file_size_bytes,
                file_type=file.content_type  # 使用 UploadFile 的 content_type
            )
            uploaded_files_metadata.append(metadata)

            # 病毒扫描占位符 (可以在 service 层或者异步任务中完成)
            print(f"TODO: 对文件 {original_filename} (存储为 {stored_filename}) 提交病毒扫描请求。")

        except HTTPException as e:
            # 如果是多个文件上传，一个文件失败了，可以选择：
            # 1. 继续上传其他文件，并最后报告哪些成功哪些失败 (当前实现倾向于此)
            # 2. 中断整个上传过程 (需要更复杂的事务处理和回滚已上传文件)
            # 这里简单地将错误信息附加到响应中，或者直接抛出让客户端知道。
            # 为了简化，如果任何文件处理失败，我们将抛出该特定文件的错误。
            # 但更好的做法是收集所有错误和成功信息。
            # 对于这个实现，我们将让单个文件的HTTPException向上冒泡。
            # 如果要收集，可以这样：
            # errors.append({"filename": file.filename, "error": e.detail})
            # continue
            raise e # 直接抛出遇到的第一个错误
        except Exception as e:
            # 其他意外错误
            # server_error_logging(e) # 假设有日志记录
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"上传文件 '{file.filename}' 时发生内部错误: {str(e)}"
            )

    if not uploaded_files_metadata:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # 或者根据是否有部分成功来调整
            detail="所有文件均未能成功上传。" # 或者提供更详细的错误报告
        )

    return uploaded_files_metadata


@router.get("/", summary="获取已上传文件列表", response_model=PaginatedFileMetadataResponse) # 或者 List[FileMetadataResponse] 如果不分页
async def get_files_list_endpoint(page: int = 1, size: int = 20):
    """
    获取已上传文件的元数据列表。
    支持分页。
    """
    # 实际应用中，分页参数会传递给 service 层，由 service 层与数据库交互实现分页
    all_metadata = await file_service.get_all_file_metadata()

    # 手动进行分页 (如果 service 层没有实现)
    start_index = (page - 1) * size
    end_index = start_index + size
    paginated_items = all_metadata[start_index:end_index]

    return PaginatedFileMetadataResponse(
        total=len(all_metadata),
        items=paginated_items,
        page=page,
        size=size
    )

@router.get("/{file_id}", summary="获取单个文件元数据", response_model=FileMetadataResponse)
async def get_file_metadata_endpoint(file_id: str):
    """
    根据文件ID（在此简化示例中为存储文件名）获取单个文件的元数据。
    """
    metadata = await file_service.get_file_metadata_by_id(file_id)
    if not metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID为 '{file_id}' 的文件元数据未找到。")
    return metadata


@router.delete("/{file_id}", summary="删除指定文件及其元数据", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(file_id: str):
    """
    根据文件ID（存储文件名）删除物理文件及其元数据。
    成功则返回 204 No Content。
    """
    success = await file_service.delete_file_and_metadata(file_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID为 '{file_id}' 的文件未找到或无法删除。")
    # 对于DELETE操作，成功时通常返回204 No Content，并且响应体为空
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/download/{file_id}", summary="下载指定文件")
async def download_file_endpoint(file_id: str):
    """
    根据文件ID（存储文件名）提供文件下载。
    """
    metadata = await file_service.get_file_metadata_by_id(file_id)
    if not metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件未找到，无法下载。")

    file_path = await file_service.get_physical_file_path(metadata.stored_filename)
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物理文件未在服务器上找到。")

    # 使用FileResponse来流式传输文件
    # original_filename 用于浏览器下载时显示的文件名
    return FileResponse(
        path=file_path,
        filename=metadata.original_filename,
        media_type=metadata.file_type or 'application/octet-stream' # 提供MIME类型
    )

# 可以在这里添加其他与文件相关的路由，例如更新元数据等
# @router.patch("/{file_id}/metadata", summary="更新文件元数据", response_model=FileMetadataResponse)
# async def update_file_metadata_endpoint(file_id: str, metadata_update: FileMetadataUpdate):
#     """
#     更新现有文件的元数据。
#     """
#     updated_metadata = await file_service.update_metadata(file_id, metadata_update)
#     if not updated_metadata:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID为 '{file_id}' 的文件元数据未找到，无法更新。")
#     return updated_metadata
