import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable, Any, Optional, List, Dict
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTaskService:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)
        self.failed_tasks: List[Dict] = []
        self.completed_tasks: List[Dict] = []
        self.pending_tasks: Dict[str, Dict] = {}
        self._is_shutdown = False

        # Start background monitor
        self._monitor_task = asyncio.create_task(self._monitor_tasks())

    async def run_in_background(self, func: Callable, *args,
                                task_id: Optional[str] = None,
                                priority: TaskPriority = TaskPriority.NORMAL,
                                **kwargs) -> Any:
        """
        Run a function in the background with proper async/sync handling
        """
        if self._is_shutdown:
            raise RuntimeError("Task service is shutting down")

        task_id = task_id or f"task_{int(time.time())}_{id(func)}"

        # Register task as pending
        self.pending_tasks[task_id] = {
            'function': func.__name__,
            'status': TaskStatus.PENDING,
            'priority': priority,
            'submitted_at': datetime.now(),
            'task_id': task_id
        }

        try:
            async with self.semaphore:
                self.pending_tasks[task_id]['status'] = TaskStatus.RUNNING

                if asyncio.iscoroutinefunction(func):
                    # Handle async functions directly
                    logger.debug(f"Executing async function: {func.__name__}")
                    result = await func(*args, **kwargs)
                else:
                    # Handle sync functions in thread pool
                    logger.debug(f"Executing sync function in thread: {func.__name__}")
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.executor,
                        lambda: func(*args, **kwargs)
                    )

                # Mark as completed
                self.pending_tasks[task_id]['status'] = TaskStatus.COMPLETED
                self.pending_tasks[task_id]['completed_at'] = datetime.now()

                self.completed_tasks.append({
                    'task_id': task_id,
                    'function': func.__name__,
                    'completed_at': datetime.now(),
                    'status': TaskStatus.COMPLETED
                })

                return result

        except Exception as e:
            # Mark as failed
            self.pending_tasks[task_id]['status'] = TaskStatus.FAILED
            self.pending_tasks[task_id]['error'] = str(e)
            self.pending_tasks[task_id]['failed_at'] = datetime.now()

            error_info = {
                'task_id': task_id,
                'function': func.__name__,
                'error': str(e),
                'timestamp': datetime.now(),
                'args': str(args),
                'kwargs': str(kwargs)
            }
            self.failed_tasks.append(error_info)
            logger.error(f"Background task failed: {func.__name__} - {e}")
            raise

    async def run_with_retry(self, func: Callable, max_retries: int = 3,
                             retry_delay: float = 1.0, *args, **kwargs) -> Any:
        """
        Run a function with exponential backoff retry logic
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await self.run_in_background(func, *args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == max_retries - 1:
                    break

                delay = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. "
                    f"Retrying in {delay:.1f}s. Error: {e}"
                )
                await asyncio.sleep(delay)

        # If we get here, all retries failed
        raise last_exception

    async def schedule_task(self, func: Callable, delay: float = 0, *args, **kwargs):
        """
        Schedule a task to run after a delay
        """
        await asyncio.sleep(delay)
        return await self.run_in_background(func, *args, **kwargs)

    async def run_batch(self, tasks: List[Callable], max_concurrent: Optional[int] = None):
        """
        Run multiple tasks concurrently with limited concurrency
        """
        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)
        else:
            semaphore = self.semaphore

        async def run_with_semaphore(task):
            async with semaphore:
                return await self.run_in_background(task)

        return await asyncio.gather(*(run_with_semaphore(task) for task in tasks))

    async def _monitor_tasks(self):
        """
        Background task to monitor and clean up completed tasks
        """
        while not self._is_shutdown:
            try:
                # Clean up old completed tasks (keep last 100)
                if len(self.completed_tasks) > 100:
                    self.completed_tasks = self.completed_tasks[-50:]

                # Clean up old failed tasks (keep last 50)
                if len(self.failed_tasks) > 50:
                    self.failed_tasks = self.failed_tasks[-25:]

                # Remove stale pending tasks (older than 1 hour)
                current_time = datetime.now()
                stale_tasks = []
                for task_id, task_info in self.pending_tasks.items():
                    if (current_time - task_info['submitted_at']).total_seconds() > 3600:
                        stale_tasks.append(task_id)

                for task_id in stale_tasks:
                    del self.pending_tasks[task_id]

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Task monitor error: {e}")
                await asyncio.sleep(60)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current task service statistics
        """
        pending_count = len([t for t in self.pending_tasks.values()
                             if t['status'] == TaskStatus.PENDING])
        running_count = len([t for t in self.pending_tasks.values()
                             if t['status'] == TaskStatus.RUNNING])

        return {
            'max_workers': self.max_workers,
            'pending_tasks': pending_count,
            'running_tasks': running_count,
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'is_shutdown': self._is_shutdown,
            'semaphore_value': self.semaphore._value
        }

    def get_failed_tasks(self, limit: int = 10) -> List[Dict]:
        """
        Get recent failed tasks
        """
        return self.failed_tasks[-limit:]

    async def shutdown(self, timeout: float = 30.0):
        """
        Gracefully shutdown the task service
        """
        if self._is_shutdown:
            return

        self._is_shutdown = True
        self._monitor_task.cancel()

        try:
            await asyncio.wait_for(self._monitor_task, timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        # Shutdown executor
        self.executor.shutdown(wait=True, timeout=timeout)
        logger.info("Background task service shutdown completed")


# Global instance
task_service = BackgroundTaskService()


# Example usage functions
async def example_async_task(data: str, delay: float = 1.0):
    """Example async task"""
    logger.info(f"Starting async task with data: {data}")
    await asyncio.sleep(delay)
    logger.info(f"Completed async task with data: {data}")
    return f"async_result_{data}"


def example_sync_task(data: str, delay: float = 1.0):
    """Example sync task"""
    logger.info(f"Starting sync task with data: {data}")
    time.sleep(delay)
    logger.info(f"Completed sync task with data: {data}")
    return f"sync_result_{data}"


# Test the service
async def test_service():
    """Test function to verify the service works"""
    try:
        # Test async function
        result1 = await task_service.run_in_background(example_async_task, "test_async")
        print(f"Async result: {result1}")

        # Test sync function
        result2 = await task_service.run_in_background(example_sync_task, "test_sync")
        print(f"Sync result: {result2}")

        # Test with retry
        result3 = await task_service.run_with_retry(example_async_task, "test_retry")
        print(f"Retry result: {result3}")

        # Get stats
        stats = task_service.get_stats()
        print(f"Service stats: {stats}")

    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        await task_service.shutdown()


if __name__ == "__main__":
    # Run test
    asyncio.run(test_service())