from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from typing import List, Dict, Any
import os
import shutil # For file operations

# Assuming services are structured to be importable like this
# Adjust paths if your project structure is different
from app.services.batch_processor import BatchProcessor
from app.services.performance_optimizer import PerformanceOptimizer
# from app.services.async_task_manager import AsyncTaskManager # If used directly by API

# --- Dependency Injection ---
# Global instances (simple DI, for more complex apps, use FastAPI's Depends with a factory)
# These should ideally be managed by the application lifecycle (e.g. lifespan events)

# In a real app, you'd initialize these carefully, perhaps with settings from a config file.
# For this example, direct instantiation.
batch_processor_service = BatchProcessor(max_concurrent_files=5) # Default, can be configured
performance_optimizer_service = PerformanceOptimizer()
# async_task_manager_service = AsyncTaskManager() # If needed directly

def get_batch_processor() -> BatchProcessor:
    return batch_processor_service

def get_performance_optimizer() -> PerformanceOptimizer:
    return performance_optimizer_service

# --- Router Definition ---
router = APIRouter()

# --- Temporary File Storage Configuration ---
# In a production environment, use a more robust solution for temporary file storage.
TEMP_UPLOAD_DIR = "temp_batch_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


@router.post("/batch/upload", summary="Upload multiple files for batch processing")
async def upload_batch_files(
    files: List[UploadFile] = File(..., description="List of files to upload"),
    job_config_str: str = Form("{}", description="JSON string for job configuration (optional)")
):
    """
    Uploads multiple files and prepares them for a batch job.
    Returns a list of server-side file paths and a suggested job configuration.
    Files are stored temporarily on the server.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    uploaded_file_paths = []
    file_errors = []

    # Create a unique sub-directory for this upload batch to avoid name collisions
    batch_upload_id = f"batch_{os.urandom(8).hex()}"
    current_batch_dir = os.path.join(TEMP_UPLOAD_DIR, batch_upload_id)
    os.makedirs(current_batch_dir, exist_ok=True)

    for file in files:
        try:
            if not file.filename:
                file_errors.append({"original_filename": "N/A", "error": "File has no name."})
                continue

            # Sanitize filename (basic) - consider more robust sanitization
            safe_filename = os.path.basename(file.filename)
            file_location = os.path.join(current_batch_dir, safe_filename)

            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)

            uploaded_file_paths.append(file_location)
        except Exception as e:
            file_errors.append({"original_filename": file.filename, "error": str(e)})
        finally:
            # Ensure the file buffer is closed, even on error
            if hasattr(file, 'file') and hasattr(file.file, 'close'):
                 file.file.close()


    if not uploaded_file_paths and file_errors:
         raise HTTPException(status_code=500, detail={"message": "All file uploads failed.", "errors": file_errors})

    import json
    try:
        job_config = json.loads(job_config_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON string for job_config.")

    return {
        "message": f"{len(uploaded_file_paths)} files uploaded successfully to batch {batch_upload_id}.",
        "uploaded_file_paths_on_server": uploaded_file_paths, # These are server paths
        "batch_upload_id": batch_upload_id, # Client can use this to refer to the set of files
        "job_config_received": job_config,
        "upload_errors": file_errors if file_errors else None
    }

@router.post("/batch/process", status_code=202, summary="Start a batch processing job")
async def start_batch_processing(
    file_paths: List[str] = Form(..., description="List of server-side file paths to process (obtained from /upload)"),
    job_config_str: str = Form("{}", description="JSON string for job configuration"),
    processor: BatchProcessor = Depends(get_batch_processor)
):
    """
    Starts a batch processing job with the provided list of (server-side) file paths and configuration.
    The actual processing happens in the background.
    """
    if not file_paths:
        raise HTTPException(status_code=400, detail="No file paths provided for processing.")

    import json
    try:
        job_config = json.loads(job_config_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON string for job_config.")

    # Validate that files exist (basic check) - more robust checks might be needed
    for fp in file_paths:
        if not os.path.exists(fp) or not fp.startswith(TEMP_UPLOAD_DIR): # Security check
            raise HTTPException(status_code=400, detail=f"File path '{fp}' is invalid or not found in allowed upload directory.")

    job_id = processor.create_batch_job(file_paths=file_paths, job_config=job_config)

    # Trigger the background processing
    # The BatchProcessor.process_batch_files is designed to be non-blocking (starts a thread)
    result = processor.process_batch_files(job_id)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=f"Failed to start batch job: {result.get('message')}")

    return {"message": "Batch processing job started.", "job_id": job_id, "details": result.get("message")}


@router.get("/batch/status/{job_id}", summary="Get the status of a batch processing job")
async def get_batch_job_status(job_id: str, processor: BatchProcessor = Depends(get_batch_processor)):
    """
    Retrieves the current status and progress of a specific batch job.
    """
    status = processor.get_batch_progress(job_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status

@router.get("/batch/report/{job_id}", summary="Get the report for a completed batch job")
async def get_batch_job_report(job_id: str, processor: BatchProcessor = Depends(get_batch_processor)):
    """
    Retrieves the final report for a completed or failed batch job.
    """
    report = processor.generate_batch_report(job_id)
    if "error" in report:
        # Distinguish between "not found" and "not yet complete"
        if "Job ID not found" in report["error"]:
            raise HTTPException(status_code=404, detail=report["error"])
        else: # e.g. "job is not yet complete"
             raise HTTPException(status_code=400, detail=report["error"])
    return report

@router.delete("/batch/cancel/{job_id}", status_code=200, summary="Cancel a running batch job")
async def cancel_batch_job_endpoint(job_id: str, processor: BatchProcessor = Depends(get_batch_processor)):
    """
    Attempts to cancel an ongoing batch processing job.
    """
    success = processor.cancel_batch_job(job_id)
    if not success:
        # Check if job exists to give a more specific error
        job_details = processor.jobs.get(job_id)
        if not job_details:
            raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found.")
        raise HTTPException(status_code=400, detail=f"Failed to cancel job '{job_id}'. It might already be completed, cancelled, or not cancelable.")
    return {"message": f"Cancellation request for job '{job_id}' processed.", "job_id": job_id, "status": "Cancellation requested"}


@router.get("/performance/metrics", summary="Get system and application performance metrics")
async def get_system_performance_metrics(optimizer: PerformanceOptimizer = Depends(get_performance_optimizer)):
    """
    Retrieves current system performance metrics, including CPU, memory, disk,
    Neo4j database metrics (mocked), and cache statistics.
    """
    metrics = optimizer.monitor_system_performance()
    if "error" in metrics:
        raise HTTPException(status_code=500, detail=f"Error fetching performance metrics: {metrics['error']}")
    return metrics

# --- Cleanup for temporary files (Example - not robust for production) ---
# In production, use a proper background task system (e.g., Celery with scheduled tasks)
# or rely on OS-level tmp cleaning. This is a very basic example.
# This is also not part of a FastAPI endpoint but a general consideration.

def cleanup_old_batch_uploads(max_age_seconds: int = 24 * 3600): # Default: 1 day
    now = time.time()
    for item_name in os.listdir(TEMP_UPLOAD_DIR):
        item_path = os.path.join(TEMP_UPLOAD_DIR, item_name)
        if os.path.isdir(item_path): # We created subdirs per batch
            try:
                dir_stat = os.stat(item_path)
                if (now - dir_stat.st_mtime) > max_age_seconds:
                    print(f"Cleaning up old batch upload directory: {item_path}")
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"Error cleaning up directory {item_path}: {e}")

# This cleanup would need to be called periodically.
# For example, using FastAPI's lifespan events or a separate scheduler.
# @app.on_event("startup")
# async def startup_event():
#     # Schedule cleanup_old_batch_uploads if using something like APScheduler
#     pass


# To make this runnable for testing, you'd include it in your main FastAPI app:
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router, prefix="/api/v1", tags=["Batch Processing & Performance"])

# If this file is run directly (e.g. for simple standalone testing of router setup)
if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(title="Batch Processing API Test")

    # Include the router
    app.include_router(router, prefix="/api/v1", tags=["Batch Processing & Performance"])

    print(f"Temporary upload directory: {os.path.abspath(TEMP_UPLOAD_DIR)}")
    print("Test API running. Endpoints available under /api/v1/")
    print("Example: POST to http://localhost:8000/api/v1/batch/upload with files.")

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # Use this if you want to test with an HTTP client like Postman or curl.
    # For programmatic testing, you'd use FastAPI's TestClient.

    # Example of how cleanup might be called (not via HTTP)
    # print("\nSimulating cleanup call (would be scheduled):")
    # cleanup_old_batch_uploads(max_age_seconds=10) # Clean anything older than 10 seconds for test

    # Shutdown services on exit (if they have shutdown methods)
    @app.on_event("shutdown")
    async def shutdown_event():
        print("FastAPI app shutting down. Cleaning up services...")
        if hasattr(batch_processor_service, 'shutdown'):
            batch_processor_service.shutdown()
        # Add other service shutdowns if needed
        # Example: Clean up the entire temp upload directory on shutdown for testing
        if os.path.exists(TEMP_UPLOAD_DIR):
            print(f"Cleaning up root temp directory: {TEMP_UPLOAD_DIR}")
            # shutil.rmtree(TEMP_UPLOAD_DIR) # Careful with this in real scenarios

    print("To run this test server: uvicorn backend.app.api.v1.endpoints.batch_processing:app --reload")
    # Assuming this file is saved at that path relative to your project root where uvicorn is run.
    # If running this file directly: uvicorn.run(app, host="0.0.0.0", port=8000)
    # For the purpose of this tool, direct uvicorn.run is fine.
    # uvicorn.run(app, host="0.0.0.0", port=8000) # Comment out for non-interactive tool use
    print("API endpoint definitions complete. To run, integrate into your main FastAPI application.")
