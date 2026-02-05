"""
Parallel Processing - Multi-Worker Execution

Parallel scraping with process and thread pools.
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Callable, Optional
import multiprocessing


class ParallelProcessor:
    """
    Multi-worker parallel processing for heavy workloads.
    
    Features:
    - Process pool for CPU-bound tasks
    - Thread pool for I/O-bound tasks
    - Async-compatible interface
    """
    
    def __init__(
        self, 
        max_processes: Optional[int] = None,
        max_threads: int = 20
    ):
        self.max_processes = max_processes or multiprocessing.cpu_count()
        self.max_threads = max_threads
        self._process_pool = None
        self._thread_pool = None
    
    def _get_process_pool(self) -> ProcessPoolExecutor:
        """Get or create process pool"""
        if self._process_pool is None:
            self._process_pool = ProcessPoolExecutor(
                max_workers=self.max_processes
            )
        return self._process_pool
    
    def _get_thread_pool(self) -> ThreadPoolExecutor:
        """Get or create thread pool"""
        if self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(
                max_workers=self.max_threads
            )
        return self._thread_pool
    
    async def map_processes(
        self, 
        func: Callable, 
        items: list,
        chunk_size: Optional[int] = None
    ) -> list:
        """
        Process items in parallel using process pool.
        
        Best for CPU-bound tasks like HTML parsing, data processing.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            chunk_size: Number of items per process
        
        Returns:
            List of results
        """
        loop = asyncio.get_event_loop()
        pool = self._get_process_pool()
        
        if chunk_size:
            # Chunked processing
            chunks = [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]
            futures = [
                loop.run_in_executor(pool, func, chunk)
                for chunk in chunks
            ]
            results = await asyncio.gather(*futures)
            # Flatten
            return [item for sublist in results for item in sublist]
        else:
            # Item-by-item
            futures = [
                loop.run_in_executor(pool, func, item)
                for item in items
            ]
            return await asyncio.gather(*futures)
    
    async def map_threads(
        self, 
        func: Callable, 
        items: list
    ) -> list:
        """
        Process items in parallel using thread pool.
        
        Best for I/O-bound tasks like network requests.
        
        Args:
            func: Function to apply to each item (can be sync)
            items: List of items to process
        
        Returns:
            List of results
        """
        loop = asyncio.get_event_loop()
        pool = self._get_thread_pool()
        
        futures = [
            loop.run_in_executor(pool, func, item)
            for item in items
        ]
        
        return await asyncio.gather(*futures, return_exceptions=True)
    
    async def run_with_semaphore(
        self, 
        coros: list,
        limit: int = 10
    ) -> list:
        """
        Run async coroutines with concurrency limit.
        
        Args:
            coros: List of coroutines
            limit: Maximum concurrent executions
        
        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(limit)
        
        async def limited(coro):
            async with semaphore:
                return await coro
        
        limited_coros = [limited(c) for c in coros]
        return await asyncio.gather(*limited_coros, return_exceptions=True)
    
    def close(self):
        """Shutdown pools"""
        if self._process_pool:
            self._process_pool.shutdown(wait=False)
        if self._thread_pool:
            self._thread_pool.shutdown(wait=False)


async def scrape_urls_parallel(
    urls: list[str],
    scrape_func: Callable,
    max_concurrent: int = 10
) -> list[dict]:
    """
    Convenience function to scrape multiple URLs in parallel.
    
    Args:
        urls: List of URLs to scrape
        scrape_func: Async function that takes URL and returns content
        max_concurrent: Maximum concurrent requests
    
    Returns:
        List of {url: str, content: str, error: str?}
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch(url):
        async with semaphore:
            try:
                content = await scrape_func(url)
                return {"url": url, "content": content}
            except Exception as e:
                return {"url": url, "error": str(e)}
    
    tasks = [fetch(url) for url in urls]
    return await asyncio.gather(*tasks)
