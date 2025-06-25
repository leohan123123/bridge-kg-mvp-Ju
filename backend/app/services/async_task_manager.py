import uuid
import time
from typing import Dict, Any, Literal
from concurrent.futures import ThreadPoolExecutor, Future

# Define task status literals
TASK_STATUS = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]

class AsyncTaskManager:
    def __init__(self, max_workers: int = 5):
        self.task_pool: Dict[str, Future] = {}
        self.task_status: Dict[str, Dict[str, Any]] = {} # task_id: {"status": TASK_STATUS, "data": ..., "submitted_at": ..., "updated_at": ...}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit_async_task(self, task_function: callable, *args, **kwargs) -> str:
        """
        Submits a function to be run asynchronously.
        task_function: The function to execute.
        *args, **kwargs: Arguments for the task_function.
        Returns task_id.
        """
        task_id = str(uuid.uuid4())

        # Wrap the original function to update status upon completion/failure
        def task_wrapper():
            try:
                self.task_status[task_id]["status"] = "RUNNING"
                self.task_status[task_id]["updated_at"] = time.time()
                result = task_function(*args, **kwargs)
                self.task_status[task_id]["status"] = "COMPLETED"
                self.task_status[task_id]["result"] = result
                self.task_status[task_id]["updated_at"] = time.time()
                return result
            except Exception as e:
                self.task_status[task_id]["status"] = "FAILED"
                self.task_status[task_id]["error"] = str(e)
                self.task_status[task_id]["updated_at"] = time.time()
                # Optionally re-raise or handle as needed
                raise

        future = self.executor.submit(task_wrapper)
        self.task_pool[task_id] = future
        current_time = time.time()
        self.task_status[task_id] = {
            "status": "PENDING",
            "submitted_at": current_time,
            "updated_at": current_time,
            "task_type": task_function.__name__ # Store function name as task_type
        }
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Gets the status of a specific task."""
        if task_id not in self.task_status:
            return {"error": "Task ID not found"}

        status_info = self.task_status[task_id].copy() # Return a copy

        # Update status if it's still PENDING and the future is done (e.g., if wrapper didn't run)
        # Or if it's RUNNING and future is done.
        future = self.task_pool.get(task_id)
        if future and future.done() and status_info["status"] in ["PENDING", "RUNNING"]:
            try:
                # Accessing future.result() will raise an exception if the task failed
                future.result()
                if status_info["status"] != "COMPLETED": # if not already set by wrapper
                    status_info["status"] = "COMPLETED"
                    status_info["updated_at"] = time.time()
            except Exception as e:
                 if status_info["status"] != "FAILED": # if not already set by wrapper
                    status_info["status"] = "FAILED"
                    status_info["error"] = str(e)
                    status_info["updated_at"] = time.time()
            self.task_status[task_id].update(status_info) # Update master record

        return status_info

    def cancel_task(self, task_id: str) -> bool:
        """Attempts to cancel a task."""
        if task_id not in self.task_pool or task_id not in self.task_status:
            return False

        future = self.task_pool[task_id]
        status_info = self.task_status[task_id]

        if status_info["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
            return False # Cannot cancel already finished or cancelled task

        # For ThreadPoolExecutor, cancel() only works if the task hasn't started running.
        # It returns False if the task is currently running and cannot be cancelled.
        # It returns True if the task was successfully cancelled (i.e., was pending).
        was_cancelled = future.cancel()

        if was_cancelled:
            status_info["status"] = "CANCELLED"
            status_info["updated_at"] = time.time()
            return True

        # If future.cancel() returns False, it might be already running.
        # We can't forcefully stop a thread in Python easily.
        # Mark as "CANCELLED" but it might complete if already running.
        # This is a soft cancel.
        if status_info["status"] == "RUNNING" and not was_cancelled :
             # It's running, can't truly cancel, but we can mark our intent.
             # The task itself would need to check for a cancellation flag if true interruption is needed.
             pass # Keep it as RUNNING or decide on a specific "CANCELLATION_REQUESTED" status

        # If it was PENDING and cancel returned True
        if status_info["status"] == "PENDING" and was_cancelled:
             status_info["status"] = "CANCELLED"
             status_info["updated_at"] = time.time()
             return True

        return False # If it's running and cancel() returned false.

    def cleanup_completed_tasks(self, max_age_seconds: int = 24 * 3600) -> int:
        """Removes information about completed, failed, or cancelled tasks older than max_age_seconds."""
        current_time = time.time()
        tasks_to_delete = []
        cleaned_count = 0

        for task_id, status_info in self.task_status.items():
            if status_info["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
                if (current_time - status_info["updated_at"]) > max_age_seconds:
                    tasks_to_delete.append(task_id)

        for task_id in tasks_to_delete:
            if task_id in self.task_status:
                del self.task_status[task_id]
            if task_id in self.task_pool:
                del self.task_pool[task_id] # Remove the future object as well
            cleaned_count += 1

        return cleaned_count

    def get_all_tasks_status(self) -> Dict[str, Dict[str, Any]]:
        """Returns status for all known tasks."""
        # Potentially update statuses before returning
        for task_id in self.task_pool.keys():
            self.get_task_status(task_id) # This will update status if needed
        return self.task_status.copy()

    def shutdown(self, wait=True):
        """Shuts down the thread pool executor."""
        self.executor.shutdown(wait=wait)

# Example usage (outside the class, for testing)
if __name__ == "__main__":
    manager = AsyncTaskManager(max_workers=2)

    def my_long_task(duration, task_name):
        print(f"Task '{task_name}' started.")
        time.sleep(duration)
        print(f"Task '{task_name}' finished.")
        return f"Result of {task_name}"

    def my_failing_task(task_name):
        print(f"Task '{task_name}' started.")
        time.sleep(1)
        raise ValueError("Something went wrong in failing task")

    task1_id = manager.submit_async_task(my_long_task, 5, task_name="Task 1 (long)")
    task2_id = manager.submit_async_task(my_long_task, 2, task_name="Task 2 (short)")
    task3_id = manager.submit_async_task(my_failing_task, task_name="Task 3 (fails)")

    print(f"Submitted task 1: {task1_id}")
    print(f"Submitted task 2: {task2_id}")
    print(f"Submitted task 3: {task3_id}")

    time.sleep(1)
    print(f"Status task 1: {manager.get_task_status(task1_id)}")
    print(f"Status task 2: {manager.get_task_status(task2_id)}")
    print(f"Status task 3: {manager.get_task_status(task3_id)}")

    # Try to cancel task 1 (might be running)
    print(f"Attempting to cancel task 1: {manager.cancel_task(task1_id)}")
    print(f"Status task 1 after cancel attempt: {manager.get_task_status(task1_id)}")


    # Wait for tasks to complete to see final statuses
    time.sleep(5)
    print(f"Status task 1 (final): {manager.get_task_status(task1_id)}")
    print(f"Status task 2 (final): {manager.get_task_status(task2_id)}")
    print(f"Status task 3 (final): {manager.get_task_status(task3_id)}")

    print(f"All tasks: {manager.get_all_tasks_status()}")

    cleaned = manager.cleanup_completed_tasks(max_age_seconds=1) # Clean tasks older than 1 second
    print(f"Cleaned up {cleaned} tasks.")
    print(f"All tasks after cleanup: {manager.get_all_tasks_status()}")

    manager.shutdown()
    print("Async manager shut down.")
