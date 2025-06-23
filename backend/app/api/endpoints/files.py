# backend/app/api/endpoints/files.py
from fastapi import APIRouter, HTTPException, Path as FastAPIPath, UploadFile, File
from typing import Dict, Any, Optional
import shutil # 用于文件操作
from pathlib import Path

from ...services.dxf_parser import DXFParserService
from ...models.bridge_component import BridgeComponent # 虽然API直接返回dict，但类型提示可能有用

router = APIRouter()

# 模拟文件存储和解析结果存储
# 在生产环境中，这应该是一个数据库或更持久的存储方案
# file_db: Dict[str, Dict[str, Any]] = {}
# key: file_id, value: {"file_path": Path, "original_filename": str, "parsed_data": Optional[Dict], "status": str, "error": Optional[str]}

# 为了简化，我们假设文件上传后会有一个唯一的 file_id，并且我们知道其路径
# 比如存储在某个固定的上传目录下
UPLOAD_DIR = Path("temp_uploads") # 临时上传目录
UPLOAD_DIR.mkdir(exist_ok=True)

# 解析结果缓存 (file_id -> parsed_data)
# 在实际应用中，这可能存储在Redis, 数据库, 或文件系统
parsed_results_cache: Dict[str, Dict[str, Any]] = {}
parse_status_cache: Dict[str, Dict[str, Any]] = {} # file_id -> {"status": "pending/processing/completed/failed", "error": "message"}


# 模拟文件上传接口 (简化版，用于测试后续解析流程)
@router.post("/upload/", summary="上传DXF文件以供后续解析")
async def upload_dxf_file(file: UploadFile = File(..., description="要上传的DXF文件")):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空。")

    if not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="只支持DXF文件格式。")

    file_id = file.filename # 使用文件名作为file_id (简化处理)
    file_location = UPLOAD_DIR / file_id

    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # 初始化解析状态
        parse_status_cache[file_id] = {"status": "uploaded", "error": None, "file_path": str(file_location)}

        return {
            "message": f"文件 '{file.filename}' 上传成功。",
            "file_id": file_id,
            "file_path": str(file_location)
        }
    except Exception as e:
        parse_status_cache[file_id] = {"status": "upload_failed", "error": str(e)}
        raise HTTPException(status_code=500, detail=f"文件上传失败: {e}")
    finally:
        file.file.close()


@router.post("/parse/{file_id}", summary="解析指定的DXF文件")
async def parse_dxf_file(
    file_id: str = FastAPIPath(..., description="通过上传接口获取的文件ID (此处为文件名)")
):
    """
    触发对指定已上传DXF文件的解析。
    在当前同步实现中，此请求会等待解析完成。
    """
    if file_id not in parse_status_cache or parse_status_cache[file_id]["status"] == "upload_failed":
        raise HTTPException(status_code=404, detail=f"文件ID '{file_id}' 未找到或上传失败。请先上传文件。")

    file_path_str = parse_status_cache[file_id].get("file_path")
    if not file_path_str:
        raise HTTPException(status_code=500, detail=f"文件 '{file_id}' 的路径信息丢失。")

    file_path = Path(file_path_str)
    if not file_path.exists():
        parse_status_cache[file_id] = {"status": "failed", "error": "文件已不存在于服务器。"}
        raise HTTPException(status_code=404, detail=f"文件 '{file_id}' 已不存在于服务器。请重新上传。")

    parse_status_cache[file_id] = {"status": "processing", "error": None, "file_path": str(file_path)}

    try:
        parser = DXFParserService(file_path=file_path)
        parsed_data = parser.parse() # 同步执行解析

        # 检查解析过程中是否有错误记录在parsed_data中
        if parsed_data.get("errors"):
            # 可以选择将解析器内部错误合并到状态中
            error_messages = "; ".join([e.get("message", "未知解析错误") for e in parsed_data["errors"]])
            parse_status_cache[file_id] = {"status": "completed_with_errors", "error": f"解析时发生错误: {error_messages}", "file_path": str(file_path)}
            # 即使有错，也缓存结果供调试
            parsed_results_cache[file_id] = parsed_data
            # 根据需求决定是否因解析器内部错误而抛出HTTPException
            # raise HTTPException(status_code=500, detail=f"文件 '{file_id}' 解析时发生错误: {error_messages}")
        else:
            parse_status_cache[file_id] = {"status": "completed", "error": None, "file_path": str(file_path)}

        parsed_results_cache[file_id] = parsed_data # 存储解析结果

        return {
            "file_id": file_id,
            "message": f"文件 '{file_id}' 解析成功。",
            "status": parse_status_cache[file_id]["status"],
            # "parsed_data_preview": { # 可以返回少量预览信息
            #     "num_components": len(parsed_data.get("bridge_components", [])),
            #     "num_errors": len(parsed_data.get("errors", []))
            # }
        }
    except FileNotFoundError as e:
        parse_status_cache[file_id] = {"status": "failed", "error": str(e)}
        raise HTTPException(status_code=404, detail=str(e))
    except ezdxf.DXFStructureError as e: # ezdxf 特有的异常
        parse_status_cache[file_id] = {"status": "failed", "error": f"DXF文件结构错误: {e}"}
        raise HTTPException(status_code=400, detail=f"文件 '{file_id}' 结构无效: {e}")
    except Exception as e:
        parse_status_cache[file_id] = {"status": "failed", "error": str(e)}
        # 在开发阶段，返回更详细的错误可能有用
        # import traceback
        # error_details = traceback.format_exc()
        # console.log(f"解析文件 {file_id} 时发生服务器内部错误: {error_details}")
        raise HTTPException(status_code=500, detail=f"解析文件 '{file_id}' 时发生服务器内部错误: {e}")


@router.get("/parse-status/{file_id}", summary="查询DXF文件的解析状态")
async def get_parse_status(
    file_id: str = FastAPIPath(..., description="文件ID")
):
    """
    获取指定DXF文件的当前解析状态。
    """
    if file_id not in parse_status_cache:
        raise HTTPException(status_code=404, detail=f"文件ID '{file_id}' 的解析状态未找到。")

    status_info = parse_status_cache[file_id]
    return {
        "file_id": file_id,
        "status": status_info.get("status", "unknown"),
        "error_message": status_info.get("error"),
        "last_updated": None # 在异步场景中，这里可以放时间戳
    }

@router.get("/parsed-data/{file_id}", summary="获取解析后的DXF数据")
async def get_parsed_dxf_data(
    file_id: str = FastAPIPath(..., description="文件ID")
):
    """
    获取指定DXF文件解析后的结构化数据。
    只有在解析成功完成后才能获取。
    """
    status_info = parse_status_cache.get(file_id)
    if not status_info:
        raise HTTPException(status_code=404, detail=f"文件ID '{file_id}' 未找到或从未开始解析。")

    if status_info["status"] not in ["completed", "completed_with_errors"]:
        raise HTTPException(status_code=400, detail=f"文件 '{file_id}' 的解析尚未完成或失败。当前状态: {status_info['status']}")

    if file_id not in parsed_results_cache:
        # 这种情况理论上不应发生，如果状态是completed但结果不在缓存中
        raise HTTPException(status_code=404, detail=f"文件 '{file_id}' 的解析结果丢失，请尝试重新解析。")

    return {
        "file_id": file_id,
        "parsed_data": parsed_results_cache[file_id]
    }

# 为了能运行这个API模块，还需要一个main.py来启动FastAPI应用 (如果还没有的话)
# 这里不创建main.py，假设项目结构中已有或后续添加。
# 示例:
# main.py
# from fastapi import FastAPI
# from backend.app.api.endpoints import files as files_api
#
# app = FastAPI(title="Bridge Engineering MVP API")
# app.include_router(files_api.router, prefix="/api/files", tags=["Files & DXF Parsing"])
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
#
# 注意: ezdxf 不是一个 async 库，同步调用 parser.parse() 会阻塞事件循环。
# 对于大文件，强烈建议在生产环境中使用后台任务 (如 Celery + Redis/RabbitMQ) 进行异步解析。
# 这里的实现是同步的，适用于MVP或小文件。
