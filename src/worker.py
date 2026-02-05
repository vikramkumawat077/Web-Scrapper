"""
Worker - 24/7 Background Job Processor

Processes scrape jobs from Redis queue.
"""

import asyncio
from typing import Optional
import json


async def run_worker(concurrency: int = 10, queue_name: str = "scrape_queue"):
    """
    Run the 24/7 worker process.
    
    Args:
        concurrency: Number of parallel workers
        queue_name: Redis queue to process
    """
    try:
        import redis.asyncio as redis
    except ImportError:
        print("❌ redis package not installed. Run: pip install redis")
        return
    
    from src.config import config
    from src.scrapers.engine_selector import smart_scrape
    from src.extractors.email_extractor import EmailExtractor
    from src.extractors.social_extractor import SocialExtractor
    
    # Connect to Redis
    r = redis.from_url(config.database.redis_url)
    
    email_extractor = EmailExtractor()
    social_extractor = SocialExtractor()
    
    print(f"🔄 Worker started with {concurrency} concurrent tasks")
    print(f"   Listening on queue: {queue_name}")
    
    async def process_job(job_data: dict) -> dict:
        """Process a single job"""
        url = job_data.get("url")
        if not url:
            return {"error": "No URL provided"}
        
        try:
            html = await smart_scrape(url)
            emails = email_extractor.extract(html)
            social = social_extractor.extract(html)
            
            return {
                "url": url,
                "success": True,
                "emails": emails,
                "social": social
            }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    # Semaphore for concurrency control
    semaphore = asyncio.Semaphore(concurrency)
    
    async def worker():
        """Worker loop"""
        while True:
            async with semaphore:
                try:
                    # Blocking pop from queue
                    result = await r.blpop(queue_name, timeout=5)
                    
                    if result:
                        _, job_json = result
                        job = json.loads(job_json)
                        
                        # Process
                        result = await process_job(job)
                        
                        # Push result
                        await r.rpush(
                            f"{queue_name}:results",
                            json.dumps(result)
                        )
                        
                        status = "✅" if result.get("success") else "❌"
                        print(f"{status} Processed: {job.get('url', 'N/A')[:50]}")
                
                except Exception as e:
                    print(f"Worker error: {e}")
                    await asyncio.sleep(1)
    
    # Run workers
    workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
    
    try:
        await asyncio.gather(*workers)
    except KeyboardInterrupt:
        print("\n👋 Shutting down worker...")
        for w in workers:
            w.cancel()
