import uuid
import time
import os
import random # For simulation
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Assuming KnowledgeGraphEngine and AsyncTaskManager are in the same directory or installable
from .knowledge_graph_engine import KnowledgeGraphEngine
from .async_task_manager import AsyncTaskManager # To be used later for actual async processing

# Job Status Constants
JOB_STATUS_PENDING = "PENDING"
JOB_STATUS_RUNNING = "RUNNING"
JOB_STATUS_COMPLETED = "COMPLETED"
JOB_STATUS_FAILED = "FAILED"
JOB_STATUS_PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
JOB_STATUS_CANCELLED = "CANCELLED" # Added


class BatchProcessor:
    def __init__(self, max_concurrent_files: int = 5):
        self.knowledge_engine = KnowledgeGraphEngine()
        self.jobs: Dict[str, Dict[str, Any]] = {} # Stores job_id -> job_details
        self.file_processor_executor = ThreadPoolExecutor(max_workers=max_concurrent_files)
        # self.async_manager = AsyncTaskManager() # Could be integrated later if needed for other async tasks

    def _process_single_file(self, file_path: str, job_config: Dict, job_id: str) -> Dict:
        """
        Internal method to process a single file.
        Checks job status for cancellation before processing.
        This will be executed by the ThreadPoolExecutor.
        """
        # Check for cancellation at the beginning of individual file processing
        current_job_status = self.jobs.get(job_id, {}).get("status")
        if current_job_status == JOB_STATUS_CANCELLED:
            return {"file_path": file_path, "status": "cancelled", "error": "Job was cancelled before processing this file."}

        try:
            if not os.path.exists(file_path):
                return {"file_path": file_path, "status": "error", "error": "File not found."}

            # Simulate reading content or getting basic info
            file_content_mock = {"size": os.path.getsize(file_path), "type": os.path.splitext(file_path)[1]}

            # Simulate interaction with KnowledgeGraphEngine
            # In a real scenario, job_config might influence processing
            # print(f"BatchProcessor: Processing file '{file_path}' with KGE for job {job_id}...") # Less verbose
            result = self.knowledge_engine.process_document_and_update_graph(file_path, document_content=file_content_mock)

            if result.get("status") == "success":
                return {"file_path": file_path, "status": "processed", "details": result.get("graph_updates", {})}
            else:
                return {"file_path": file_path, "status": "error", "error": result.get("message", "KGE processing failed")}

        except Exception as e:
            return {"file_path": file_path, "status": "error", "error": str(e)}

    def create_batch_job(self, file_paths: List[str], job_config: Dict) -> str:
        """Creates a batch processing job and returns its ID."""
        job_id = str(uuid.uuid4())
        timestamp = time.time()

        self.jobs[job_id] = {
            "job_id": job_id,
            "file_paths": file_paths, # Original list of files for the job
            "job_config": job_config,
            "status": JOB_STATUS_PENDING,
            "created_at": timestamp,
            "started_at": None,
            "completed_at": None,
            "total_files": len(file_paths),
            "processed_files_count": 0,
            "successful_files_count": 0,
            "failed_files_count": 0,
            "cancelled_files_count": 0, # New counter
            "results": [], # List of dicts for each file's outcome
            "errors": [] # List of dicts for each file's error if any
        }
        print(f"Batch job {job_id} created for {len(file_paths)} files.")
        return job_id

    def process_batch_files(self, job_id: str) -> Dict:
        """
        Starts the execution of a batch file processing job in a background thread.
        Returns immediately. Status can be polled via get_batch_progress.
        """
        job = self.jobs.get(job_id)
        if not job:
            return {"status": "error", "message": "Job ID not found."}

        if job["status"] not in [JOB_STATUS_PENDING, JOB_STATUS_PARTIAL_SUCCESS, JOB_STATUS_FAILED, JOB_STATUS_CANCELLED]: # Allow retry/restart
            return {"status": "error", "message": f"Job already in status: {job['status']}. Cannot restart unless it's PENDING, FAILED, PARTIAL_SUCCESS, or CANCELLED."}

        # Reset job state for a fresh run or retry
        job["status"] = JOB_STATUS_RUNNING
        job["started_at"] = time.time()
        job["completed_at"] = None
        job["results"] = []
        job["errors"] = []
        job["processed_files_count"] = 0
        job["successful_files_count"] = 0
        job["failed_files_count"] = 0
        job["cancelled_files_count"] = 0


        def _run_job_async_wrapper():
            """Wraps the actual job execution to handle overall job errors and status updates."""
            try:
                # Create a list of futures for file processing tasks
                # Pass job_id to _process_single_file for cancellation checks
                futures_map = {
                    self.file_processor_executor.submit(self._process_single_file, fp, job["job_config"], job_id): fp
                    for fp in job["file_paths"]
                }

                for future in as_completed(futures_map):
                    file_path = futures_map[future]

                    # Primary check: if job itself was cancelled during processing of other files
                    if job["status"] == JOB_STATUS_CANCELLED:
                        # If job is cancelled, we might still get results from futures that were already running
                        # or we can try to cancel pending futures (though ThreadPoolExecutor's cancel is limited)
                        # For simplicity, we'll let already submitted tasks run but mark files not yet processed as cancelled.
                        # The _process_single_file should also check this status internally.
                        # The loop will continue for already running/queued tasks from before cancellation.
                        # This logic might need refinement if we want to aggressively stop queueing.
                        # However, ThreadPoolExecutor doesn't offer easy removal of queued tasks by group.
                        # The `future.cancel()` could be attempted here for pending tasks, but it's not guaranteed.
                        pass # Individual file processing will handle its own "cancelled" status if it checks job status

                    try:
                        result = future.result() # Get result from individual file processing
                        job["results"].append(result)

                        if result["status"] == "processed":
                            job["successful_files_count"] += 1
                        elif result["status"] == "cancelled": # File processing was skipped due to job cancellation
                            job["cancelled_files_count"] +=1
                        else: # error
                            job["failed_files_count"] += 1
                            job["errors"].append({"file_path": file_path, "reason": result.get("error", "Unknown error")})

                    except Exception as exc: # Exception from the future.result() call itself (e.g., task failed unexpectedly)
                        job["failed_files_count"] += 1
                        job["errors"].append({"file_path": file_path, "reason": f"Task execution error: {str(exc)}"})
                    finally:
                        # This count includes successful, failed, and individually cancelled files that were attempted.
                        job["processed_files_count"] = job["successful_files_count"] + job["failed_files_count"] + job["cancelled_files_count"]


                # Final job status determination
                if job["status"] == JOB_STATUS_CANCELLED:
                    # If it was externally cancelled, keep CANCELLED status.
                    # Account for any files that were never even submitted to the executor if cancellation was very fast.
                    unaccounted_files = job["total_files"] - job["processed_files_count"]
                    if unaccounted_files > 0:
                        job["cancelled_files_count"] += unaccounted_files
                        job["processed_files_count"] = job["total_files"] # Mark all as "accounted for"

                elif job["failed_files_count"] == 0 and job["cancelled_files_count"] == 0 and job["successful_files_count"] == job["total_files"]:
                    job["status"] = JOB_STATUS_COMPLETED
                elif job["successful_files_count"] > 0: # If there's any success, it's partial (could also have fails/cancels)
                    job["status"] = JOB_STATUS_PARTIAL_SUCCESS
                # If job was not externally cancelled and had no successes, it's FAILED
                # (this includes cases where all files failed, or all were internally cancelled then some failed)
                elif job["status"] != JOB_STATUS_CANCELLED and job["successful_files_count"] == 0 :
                    job["status"] = JOB_STATUS_FAILED

            except Exception as e: # Catch errors in the _run_job_async_wrapper itself
                print(f"Error in batch job {job_id} execution thread: {e}")
                job["status"] = JOB_STATUS_FAILED
                job["errors"].append({"file_path": "N/A - Job Level Error", "reason": f"Job execution wrapper error: {str(e)}"})
            finally:
                job["completed_at"] = time.time()
                print(f"Batch job {job_id} thread finished. Final Status: {job['status']}")

        import threading
        job_runner_thread = threading.Thread(target=_run_job_async_wrapper, daemon=True)
        job_runner_thread.start()

        return {"status": "success", "message": f"Job {job_id} processing initiated in background."}


    def get_batch_progress(self, job_id: str) -> Dict:
        """Gets the progress of a specific batch job."""
        job = self.jobs.get(job_id)
        if not job:
            return {"error": "Job ID not found"}

        total_files = job["total_files"]
        # processed_files_count is now sum of successful, failed, and individually cancelled files
        processed_and_accounted_for = job["processed_files_count"]

        remaining_to_process_actively = total_files - processed_and_accounted_for
        estimated_remaining_time = "N/A"

        if job["status"] == JOB_STATUS_RUNNING and processed_and_accounted_for > 0 :
            # Only estimate if there are files actually remaining to be processed by workers
            if remaining_to_process_actively > 0 :
                elapsed_time = time.time() - job["started_at"]
                # Base time_per_file on files that weren't just marked 'cancelled' without an attempt
                attempted_files = job["successful_files_count"] + job["failed_files_count"]
                if attempted_files > 0:
                    time_per_file = elapsed_time / attempted_files
                    estimated_remaining_time = round(time_per_file * remaining_to_process_actively, 2)
                else: # Not enough data to estimate yet (e.g. all files so far were 'cancelled' by flag)
                    estimated_remaining_time = "Calculating..."
            else: # All files accounted for, but job status might not be final yet
                 estimated_remaining_time = 0
        elif job["status"] not in [JOB_STATUS_PENDING, JOB_STATUS_RUNNING]: # Completed, Failed, Partial, Cancelled
             estimated_remaining_time = 0


        return {
            "job_id": job_id,
            "status": job["status"],
            "total_files": total_files,
            "processed_files_count": processed_and_accounted_for, # Total files handled (processed, failed, or skipped due to cancel)
            "successful_files_count": job["successful_files_count"],
            "failed_files_count": job["failed_files_count"],
            "cancelled_files_count": job.get("cancelled_files_count", 0), # Files skipped due to cancellation
            "estimated_remaining_time_seconds": estimated_remaining_time,
            "started_at": job.get("started_at"),
            "completed_at": job.get("completed_at"),
        }

    def handle_batch_errors(self, job_id: str) -> List[Dict]:
        """Returns a list of errors for a specific batch job."""
        job = self.jobs.get(job_id)
        if not job:
            return [{"error": "Job ID not found"}]
        return job.get("errors", []) # This contains reasons for failed files

    def generate_batch_report(self, job_id: str) -> Dict:
        """Generates a report for a completed, partially completed, failed or cancelled batch job."""
        job = self.jobs.get(job_id)
        if not job:
            return {"error": "Job ID not found"}

        # Report can be generated for any terminal state, or even running state if desired (though less common)
        if job["status"] == JOB_STATUS_PENDING:
             return {"error": f"Job {job_id} has not started yet. Current status: {job['status']}"}
        # if job["status"] == JOB_STATUS_RUNNING:
        #    return {"message": "Job is still running. This is a preliminary report.", **self.get_batch_progress(job_id)}


        total_duration = None
        if job.get("started_at") and job.get("completed_at"):
            total_duration = round(job["completed_at"] - job["started_at"], 2)

        success_rate_based_on_attempted = 0
        attempted_files = job["successful_files_count"] + job["failed_files_count"]
        if attempted_files > 0:
            success_rate_based_on_attempted = round((job["successful_files_count"] / attempted_files) * 100, 2)

        completion_rate_based_on_total = 0
        if job["total_files"] > 0:
            completion_rate_based_on_total = round((job["successful_files_count"] / job["total_files"]) * 100, 2)


        # This would ideally be based on actual data from KGE if results were aggregated.
        aggregated_graph_stats = {
            "total_nodes_added_in_batch": job.get("successful_files_count", 0) * 5, # Mock based on successful
            "total_relationships_added_in_batch": job.get("successful_files_count", 0) * 10, # Mock
            "notes": "These are simulated aggregated stats."
        }

        return {
            "job_id": job_id,
            "status": job["status"],
            "total_files": job["total_files"],
            "processed_files_count": job["processed_files_count"], # Files that went through processing attempt or were skipped by cancel
            "successful_files_count": job["successful_files_count"],
            "failed_files_count": job["failed_files_count"],
            "cancelled_files_count": job.get("cancelled_files_count", 0),
            "success_rate_of_attempted_files_percentage": success_rate_based_on_attempted,
            "completion_rate_of_total_files_percentage": completion_rate_based_on_total,
            "total_processing_time_seconds": total_duration,
            "started_at": job.get("started_at"),
            "completed_at": job.get("completed_at"),
            "job_config": job.get("job_config"),
            "detailed_file_results": job.get("results", []),
            "error_summary": job.get("errors", []), # Summary of errors for failed files
            "aggregated_graph_statistics": aggregated_graph_stats
        }

    def cancel_batch_job(self, job_id: str) -> bool:
        """
        Marks a job as CANCELLED.
        If the job is PENDING, it won't start processing.
        If the job is RUNNING, its status is set to CANCELLED. The background processing
        loop (_run_job_async_wrapper) and individual file tasks (_process_single_file)
        will check this status. Tasks already submitted to the ThreadPoolExecutor might still run,
        but new processing for files within _process_single_file should halt if it checks the status.
        The _run_job_async_wrapper will ensure the job eventually finalizes.
        """
        job = self.jobs.get(job_id)
        if not job:
            print(f"Cancel request for non-existent job ID: {job_id}")
            return False

        if job["status"] == JOB_STATUS_PENDING:
            job["status"] = JOB_STATUS_CANCELLED
            job["completed_at"] = time.time() # Mark as completed now since it won't run
            job["cancelled_files_count"] = job["total_files"] # All files are considered cancelled
            job["processed_files_count"] = job["total_files"]
            print(f"Pending job {job_id} was cancelled before starting. All files marked as cancelled.")
            return True
        elif job["status"] == JOB_STATUS_RUNNING:
            job["status"] = JOB_STATUS_CANCELLED
            # The 'completed_at' will be set by _run_job_async_wrapper when it finishes.
            print(f"Job {job_id} has been marked as CANCELLED. Its background thread will handle graceful termination of tasks.")
            # Note: This doesn't forcefully stop threads in ThreadPoolExecutor.
            # The cooperative cancellation relies on _process_single_file and _run_job_async_wrapper
            # checking the job["status"].
            return True

        print(f"Job {job_id} is already in a terminal state ({job['status']}) or cannot be cancelled. No action taken.")
        return False


    def shutdown(self):
        """Shuts down the internal ThreadPoolExecutor. Call this on application exit."""
        print("BatchProcessor shutting down file processor executor...")
        self.file_processor_executor.shutdown(wait=True) # Wait for existing file tasks to complete
        print("File processor executor shut down.")
        # Any running _run_job_async_wrapper threads are daemonic and will exit if the main app exits,
        # but ideally, they should complete their current job finalization.
        # For very robust shutdown, one might track these job threads and join them,
        # but that adds complexity if jobs are long-running post-cancellation.


# Example Usage (for testing)
if __name__ == "__main__":
    import shutil # For cleanup

    processor = BatchProcessor(max_concurrent_files=3) # Test with 3 concurrent files

    # Create some dummy files for testing
    test_files_dir = "temp_batch_files"
    os.makedirs(test_files_dir, exist_ok=True)
    mock_file_paths = []
    for i in range(5): # Create 5 initial files
        fp = os.path.join(test_files_dir, f"doc_{i+1}.txt")
        with open(fp, "w") as f:
            f.write(f"This is content for document {i+1}.")
        mock_file_paths.append(fp)

    # Add a file that might cause a simulated error in KGE
    error_file_path = os.path.join(test_files_dir, "error_doc.txt") # This is the 6th file
    with open(error_file_path, "w") as f:
        f.write("This document will cause a KGE error.")
    mock_file_paths.append(error_file_path)

    # Add a non-existent file path
    mock_file_paths.append(os.path.join(test_files_dir, "non_existent_doc.txt")) # 7th file


    print("--- Creating Batch Job (job_1) ---")
    job_1_id = processor.create_batch_job(file_paths=mock_file_paths, job_config={"mode": "full_analysis"})
    print(f"Batch job created with ID: {job_1_id}")

    print("\n--- Starting Batch Processing for job_1 ---")
    start_result = processor.process_batch_files(job_1_id)
    print(f"Process start result for job_1: {start_result}")

    print("\n--- Monitoring Progress for job_1 (will poll a few times) ---")
    for i in range(20): # Poll for up to ~10 seconds (0.5s sleep)
        progress = processor.get_batch_progress(job_1_id)
        print(f"Job 1 Progress (Attempt {i+1}): {progress}")
        if progress.get("status") not in [JOB_STATUS_PENDING, JOB_STATUS_RUNNING]:
            print(f"Job {job_1_id} reached terminal state: {progress.get('status')}")
            break
        time.sleep(0.5)

    print("\n--- Handling Errors for job_1 ---")
    errors = processor.handle_batch_errors(job_1_id)
    if errors:
        print(f"Errors found for job_1 ({len(errors)}):")
        for err in errors:
            print(f"  File: {err.get('file_path', 'N/A')}, Reason: {err.get('reason', 'N/A')}")
    else:
        print(f"No errors reported for job {job_1_id}.")

    print("\n--- Generating Report for job_1 ---")
    report = processor.generate_batch_report(job_1_id)
    print(f"Batch Report for job_1:")
    for key, value in report.items():
        if isinstance(value, list) and key in ["detailed_file_results", "error_summary"]:
             print(f"  {key}: (Count: {len(value)})")
        else:
            print(f"  {key}: {value}")

    # Test cancellation of a running job
    print("\n--- Testing Job Cancellation (job_2 - RUNNING job) ---")
    # Create a job with more files to give it time to be running
    long_job_files = []
    for i in range(10): # 10 files for job_2
        fp = os.path.join(test_files_dir, f"long_doc_{i+1}.txt")
        with open(fp, "w") as f: f.write(f"Content for long doc {i+1}")
        long_job_files.append(fp)

    job_2_id = processor.create_batch_job(file_paths=long_job_files, job_config={"type": "cancellation_test"})
    print(f"Created job for cancellation test: {job_2_id}")
    processor.process_batch_files(job_2_id)

    print(f"Waiting a bit for job {job_2_id} to start processing files...")
    time.sleep(0.2) # KGE mock is 0.1s, executor is 3 workers. Some should start.

    print(f"Attempting to cancel job {job_2_id}...")
    cancel_success = processor.cancel_batch_job(job_2_id)
    print(f"Cancellation request for job {job_2_id} was {'successful' if cancel_success else 'not successful (e.g. already terminal or not found)'}.")

    print(f"Monitoring job {job_2_id} after cancellation request...")
    for i in range(15): # Poll for a bit
        progress = processor.get_batch_progress(job_2_id)
        print(f"Job 2 Progress (Attempt {i+1}): {progress}")
        if progress.get("status") == JOB_STATUS_CANCELLED:
            print(f"Job {job_2_id} is now CANCELLED.")
            break
        if progress.get("status") not in [JOB_STATUS_RUNNING, JOB_STATUS_PENDING]: # Should not happen if cancel worked as RUNNING->CANCELLED
            print(f"Job {job_2_id} reached unexpected terminal state: {progress.get('status')}")
            break
        time.sleep(0.5) # Wait for tasks to finish or be marked cancelled by the wrapper

    final_report_cancelled_job = processor.generate_batch_report(job_2_id)
    print(f"\nFinal Report for Cancelled Job {job_2_id}:")
    for key, value in final_report_cancelled_job.items():
         if isinstance(value, list) and key in ["detailed_file_results", "error_summary"]:
             print(f"  {key}: (Count: {len(value)})")
         else:
            print(f"  {key}: {value}")

    # Test cancelling a PENDING job
    print("\n--- Testing Job Cancellation (job_3 - PENDING job) ---")
    job_3_id = processor.create_batch_job(file_paths=mock_file_paths[:2], job_config={"type": "pending_cancel_test"})
    print(f"Created PENDING job: {job_3_id}")
    cancel_pending_success = processor.cancel_batch_job(job_3_id)
    print(f"Cancellation of PENDING job {job_3_id} was {'successful' if cancel_pending_success else 'not successful'}.")
    pending_job_status = processor.get_batch_progress(job_3_id)
    print(f"Status of PENDING job {job_3_id} after cancel attempt: {pending_job_status}")
    report_pending_cancelled = processor.generate_batch_report(job_3_id)
    print(f"Report for PENDING cancelled job {job_3_id}: {report_pending_cancelled.get('status')}, cancelled files: {report_pending_cancelled.get('cancelled_files_count')}")


    processor.shutdown() # Important to allow threads to exit cleanly

    print("\n--- Cleaning up dummy files ---")
    if os.path.exists(test_files_dir):
        shutil.rmtree(test_files_dir) # Remove the whole directory and its contents
    print("Dummy files and directory cleaned up.")
    print("BatchProcessor example usage finished.")
