# backend/app/api/endpoints/preprocessing.py
import uuid
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File as FastAPIFile
from typing import Dict, Any, Optional
from pathlib import Path

from backend.app.services.file_service import FileService
from backend.app.services.dxf_parser import DXFParserService
from backend.app.services.data_preprocessor import DataPreprocessorService
from backend.app.core.config import settings # 用于获取上传目录等配置

router = APIRouter()

# 任务存储 (内存中，用于演示目的)
# 生产环境中应使用更持久的存储，如Redis, Celery backend, DB等
tasks_db: Dict[str, Dict[str, Any]] = {}

# --- Helper Functions ---

def get_file_service():
    """依赖注入：获取文件服务实例"""
    return FileService(upload_dir=settings.UPLOAD_DIRECTORY)

def run_preprocessing_task(
    task_id: str,
    file_path: Path,
    file_id: str,
    original_filename: str
):
    """
    实际执行数据预处理的后台任务函数。
    """
    tasks_db[task_id]["status"] = "processing"
    tasks_db[task_id]["message"] = "DXF文件解析开始..."

    # 确保在此作用域内 ezdxf 和其异常是可用的
    current_ezdxf_module = globals().get('ezdxf')
    DXFStructureError_to_catch = Exception # 默认为通用异常
    if current_ezdxf_module and hasattr(current_ezdxf_module, 'DXFStructureError'):
        DXFStructureError_to_catch = current_ezdxf_module.DXFStructureError

    try:
        print(f"任务 {task_id}: 开始处理文件 {file_path}")
        # 1. 解析DXF文件
        if not current_ezdxf_module: # 如果ezdxf未能导入
            raise ImportError("ezdxf库未加载，无法执行DXF解析。")

        parser = DXFParserService(file_path=str(file_path))
        parsed_data = parser.parse()
        tasks_db[task_id]["message"] = "DXF文件解析完成，开始数据预处理..."

        # 检查解析错误
        if parsed_data.get("errors"):
            # 如果解析阶段就有错误，可能需要提前标记或特殊处理
            tasks_db[task_id]["status"] = "partial_failure" # 或者 "failure"
            tasks_db[task_id]["message"] = "DXF文件解析时发生错误。"
            # 即使解析出错，也尝试进行预处理，预处理器应能处理这种情况

        # 2. 数据预处理
        preprocessor = DataPreprocessorService(parsed_dxf_data=parsed_data)
        processed_result = preprocessor.process()
        tasks_db[task_id]["message"] = "数据预处理完成。"

        # 3. 存储结果
        # 只有在之前没有因为解析错误设置为 partial_failure 时才设置为 completed
        if tasks_db[task_id]["status"] != "partial_failure":
            tasks_db[task_id]["status"] = "completed"

        tasks_db[task_id]["result"] = processed_result
        tasks_db[task_id]["original_filename"] = original_filename
        tasks_db[task_id]["file_id"] = file_id

        print(f"任务 {task_id}: 处理完成。状态: {tasks_db[task_id]['status']}")

    except FileNotFoundError as e:
        tasks_db[task_id]["status"] = "failure"
        tasks_db[task_id]["message"] = f"文件未找到: {file_path}"
        tasks_db[task_id]["error_details"] = str(e)
        print(f"任务 {task_id}: 文件未找到错误 - {file_path} - {e}")
    except DXFStructureError_to_catch as e:
        tasks_db[task_id]["status"] = "failure"
        tasks_db[task_id]["message"] = "DXF文件结构错误，无法解析。"
        tasks_db[task_id]["error_details"] = str(e)
        print(f"任务 {task_id}: DXF结构错误 - {e}")
    except ImportError as e: # 捕获由 ezdxf 未加载引起的导入错误
        tasks_db[task_id]["status"] = "failure"
        tasks_db[task_id]["message"] = f"预处理依赖项错误: {str(e)}"
        tasks_db[task_id]["error_details"] = str(e)
        print(f"任务 {task_id}: 依赖项错误 - {e}")
    except Exception as e:
        tasks_db[task_id]["status"] = "failure"
        tasks_db[task_id]["message"] = "预处理过程中发生未知错误。"
        tasks_db[task_id]["error_details"] = str(e)
        print(f"任务 {task_id}: 未知错误 - {e}")


# --- API Endpoints ---

@router.post("/process/{file_id}", status_code=202)
async def process_file_by_id(
    file_id: str, # 路径参数
    background_tasks: BackgroundTasks,
    file_service: FileService = Depends(get_file_service)
):
    """
    通过文件ID启动指定已上传文件的数据预处理任务（异步）。

    - **file_id**: 要处理的文件的唯一ID (路径参数)。
    文件应已通过 `/files/upload` 端点上传。
    """
    try:
        file_metadata = file_service.get_file_metadata(file_id)
        if not file_metadata:
            raise HTTPException(status_code=404, detail=f"文件ID {file_id} 未找到元数据。")

        file_path = Path(file_metadata["full_path"])
        original_filename = file_metadata["filename"]

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件 {original_filename} (ID: {file_id}) 未在服务器上找到。")

    except HTTPException:
        raise # 重新抛出HTTPException
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息时出错: {str(e)}")

    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {
        "status": "pending",
        "message": "任务已加入队列等待处理。",
        "file_id": file_id,
        "original_filename": original_filename,
        "task_id": task_id
    }

    background_tasks.add_task(run_preprocessing_task, task_id, file_path, file_id, original_filename)

    return {
        "task_id": task_id,
        "status": "pending",
        "message": f"文件 {original_filename} 的预处理任务已启动。",
        "file_id": file_id
    }

@router.post("/process_upload/", status_code=202)
async def upload_and_process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(..., description="要上传和处理的DXF文件。"),
    file_service: FileService = Depends(get_file_service)
):
    """
    上传DXF文件并立即开始数据预处理任务（异步）。
    这是一个便利的端点，它将文件上传和启动预处理合并为一步。

    - **file**: 从请求体中获取的上传文件。
    """
    try:
        # 先保存文件
        saved_file_metadata = await file_service.save_file(file)
        file_id = saved_file_metadata["file_id"]
        file_path = Path(saved_file_metadata["full_path"])
        original_filename = saved_file_metadata["filename"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传或保存失败: {str(e)}")

    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {
        "status": "pending",
        "message": "任务已加入队列等待处理。",
        "file_id": file_id,
        "original_filename": original_filename,
        "task_id": task_id
    }

    # 使用后台任务执行预处理
    background_tasks.add_task(run_preprocessing_task, task_id, file_path, file_id, original_filename)

    return {
        "task_id": task_id,
        "status": "pending",
        "message": f"文件 {original_filename} 的预处理任务已启动。",
        "file_id": file_id,
        "upload_info": saved_file_metadata # 也可返回上传信息
    }


@router.get("/status/{task_id}", summary="查询预处理任务的状态")
async def get_task_status(task_id: str):
    """
    根据任务ID查询异步预处理任务的当前状态。

    - **task_id**: 要查询状态的任务的唯一ID (路径参数)。
    """
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到。")

    response = {
        "task_id": task_id,
        "status": task.get("status"),
        "message": task.get("message"),
        "file_id": task.get("file_id"),
        "original_filename": task.get("original_filename")
    }
    if task.get("status") == "failure" and task.get("error_details"):
        response["error_details"] = task.get("error_details")

    return response

@router.get("/results/{task_id}", summary="获取预处理任务的完整结果")
async def get_task_results(task_id: str):
    """
    获取指定任务ID的完整预处理结果。
    结果通常包含处理后的结构化数据、数据质量报告以及任何处理错误。
    建议在任务状态为 'completed' 或 'partial_failure' 时调用此接口。

    - **task_id**: 要获取结果的任务的唯一ID (路径参数)。
    """
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到。")

    if task.get("status") == "processing" or task.get("status") == "pending":
        raise HTTPException(status_code=202, detail=f"任务仍在处理中或等待处理。当前状态: {task.get('status')}")

    if task.get("status") == "failure":
        return {
            "task_id": task_id,
            "status": "failure",
            "message": task.get("message", "任务失败，无详细信息。"),
            "error_details": task.get("error_details", "无错误详情。"),
            "file_id": task.get("file_id"),
            "original_filename": task.get("original_filename")
        }

    if task.get("status") != "completed" and task.get("status") != "partial_failure":
         raise HTTPException(status_code=400, detail=f"任务状态为 {task.get('status')}，无法获取结果。")

    # 结果中不直接返回非常大的 "processed_data" 下的 "bridge_components" 列表，
    # 而是提供一个摘要或指示。实际应用中可能需要分页或选择性字段返回。
    # 这里为了演示，我们返回完整结果，但要注意潜在的性能问题。
    result_payload = task.get("result", {})

    # 可选：对结果进行一些瘦身，例如不返回原始解析实体
    if "processed_data" in result_payload and "modelspace_entities" in result_payload["processed_data"]:
        del result_payload["processed_data"]["modelspace_entities"]


    return {
        "task_id": task_id,
        "status": task.get("status"),
        "file_id": task.get("file_id"),
        "original_filename": task.get("original_filename"),
        "data": result_payload # 包含 processed_data, quality_report, processing_errors 等
    }

@router.get("/quality-report/{task_id}", summary="获取预处理任务的数据质量报告")
async def get_task_quality_report(task_id: str):
    """
    获取指定任务ID的数据质量评估报告。
    建议在任务状态为 'completed' 或 'partial_failure' 时调用此接口。

    - **task_id**: 要获取质量报告的任务的唯一ID (路径参数)。
    """
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到。")

    if task.get("status") == "processing" or task.get("status") == "pending":
        raise HTTPException(status_code=202, detail=f"任务仍在处理中或等待处理。当前状态: {task.get('status')}")

    if task.get("status") == "failure":
        return {
            "task_id": task_id,
            "status": "failure",
            "message": task.get("message", "任务失败，无法生成质量报告。"),
            "error_details": task.get("error_details"),
            "file_id": task.get("file_id"),
            "original_filename": task.get("original_filename"),
            "quality_report": None
        }

    if task.get("status") != "completed" and task.get("status") != "partial_failure":
         raise HTTPException(status_code=400, detail=f"任务状态为 {task.get('status')}，无法获取质量报告。")

    result_payload = task.get("result", {})
    quality_report = result_payload.get("quality_report", {"message": "质量报告不可用。"})

    return {
        "task_id": task_id,
        "status": task.get("status"),
        "file_id": task.get("file_id"),
        "original_filename": task.get("original_filename"),
        "quality_report": quality_report
    }

# 需要导入 ezdxf 用于异常处理
try:
    import ezdxf
except ImportError:
    # 如果在没有ezdxf的环境中（例如，仅测试API路由结构），这可以防止启动时崩溃
    # 但在实际运行时，ezdxf是必需的
    class DXFStructureError(Exception): pass
    ezdxf = None
    print("警告: ezdxf库未找到。DXF解析功能将不可用。")

# 确保导入FileService会用到的settings
# from backend.app.core.config import settings (已在顶部导入)
# 确保导入APIRouter会用到的相关FastAPI组件 (已在顶部导入)
# from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File as FastAPIFile
# from typing import Dict, Any
# import uuid
# from pathlib import Path
# from backend.app.services.file_service import FileService
# from backend.app.services.dxf_parser import DXFParserService
# from backend.app.services.data_preprocessor import DataPreprocessorService
