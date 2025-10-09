import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable
from queue import Queue


class BackgroundTaskService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.task_queue = Queue()
        self.failed_tasks = []

    async def run_with_retry(self, func: Callable, max_retries=3, *args, **kwargs):
        for attempt in range(max_retries):
            try:
                return await self.run_in_background(func, *args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    self.failed_tasks.append({
                        'function': func.__name__,
                        'error': str(e),
                        'timestamp': datetime.now()
                    })
                    raise
                await asyncio.sleep(2 ** attempt)


task_service = BackgroundTaskService()