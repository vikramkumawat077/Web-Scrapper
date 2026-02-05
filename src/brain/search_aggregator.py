"""
Search Aggregator - Multi-Source Search Engine

Aggregates results from multiple search APIs:
- Serper (Google)
- Bing
- DuckDuckGo
- Brave
"""

import asyncio
import httpx
from typing import Optional
from src.config import config


class SearchAggregator:
    """
    Multi-source search aggregator for maximum coverage.
    
    Combines results from multiple search engines to:
    1. Maximize discovery (different engines find different results)
    2. Provide redundancy (if one API fails, others work)
    3. Deduplicate across sources
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search(self, query: str, max_results: int = 100) -> list[dict]:
        """
        Search across all available sources.
        
        Args:
            query: Search query
            max_results: Maximum results per source
        
        Returns:
            Aggregated search results
        """
        # Run all searches in parallel
        tasks = []
        
        if config.search.serper_api_key:
            tasks.append(self._search_serper(query, max_results))
        
        if config.search.bing_api_key:
            tasks.append(self._search_bing(query, max_results))
        
        if config.search.brave_api_key:
            tasks.append(self._search_brave(query, max_results))
        
        # Always include free sources
        tasks.append(self._search_duckduckgo(query, max_results))
        
        # Gather all results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and combine
        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                # Log but continue
                print(f"Search error: {result}")
        
        return all_results
    
    async def _search_serper(self, query: str, max_results: int) -> list[dict]:
        """Search using Serper.dev (Google results)"""
        try:
            response = await self.client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": config.search.serper_api_key},
                json={
                    "q": query,
                    "num": min(max_results, 100)
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic", []):
                results.append({
                    "url": item.get("link"),
                    "title": item.get("title"),
                    "snippet": item.get("snippet", ""),
                    "source": "serper"
                })
            return results
        except Exception as e:
            print(f"Serper error: {e}")
            return []
    
    async def _search_bing(self, query: str, max_results: int) -> list[dict]:
        """Search using Bing Web Search API"""
        try:
            response = await self.client.get(
                "https://api.bing.microsoft.com/v7.0/search",
                headers={"Ocp-Apim-Subscription-Key": config.search.bing_api_key},
                params={
                    "q": query,
                    "count": min(max_results, 50)
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("webPages", {}).get("value", []):
                results.append({
                    "url": item.get("url"),
                    "title": item.get("name"),
                    "snippet": item.get("snippet", ""),
                    "source": "bing"
                })
            return results
        except Exception as e:
            print(f"Bing error: {e}")
            return []
    
    async def _search_brave(self, query: str, max_results: int) -> list[dict]:
        """Search using Brave Search API"""
        try:
            response = await self.client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "X-Subscription-Token": config.search.brave_api_key,
                    "Accept": "application/json"
                },
                params={
                    "q": query,
                    "count": min(max_results, 20)
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "url": item.get("url"),
                    "title": item.get("title"),
                    "snippet": item.get("description", ""),
                    "source": "brave"
                })
            return results
        except Exception as e:
            print(f"Brave error: {e}")
            return []
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> list[dict]:
        """Search using DuckDuckGo (free, no API key)"""
        try:
            # DuckDuckGo instant answer API (limited but free)
            response = await self.client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1
                }
            )
            data = response.json()
            
            results = []
            
            # Get related topics
            for item in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(item, dict) and "FirstURL" in item:
                    results.append({
                        "url": item.get("FirstURL"),
                        "title": item.get("Text", "")[:100],
                        "snippet": item.get("Text", ""),
                        "source": "duckduckgo"
                    })
            
            return results
        except Exception as e:
            print(f"DuckDuckGo error: {e}")
            return []
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
