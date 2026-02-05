"""
Brain Layer - Autonomous Website Discovery

The brain layer automatically discovers relevant websites from keywords.
"""

import asyncio
from typing import Optional
from dataclasses import dataclass

from src.brain.search_aggregator import SearchAggregator
from src.brain.platform_harvester import PlatformHarvester
from src.brain.relevance_filter import RelevanceFilter
from src.config import config


@dataclass
class DiscoveredSite:
    """Represents a discovered website"""
    url: str
    title: str
    snippet: str
    source: str
    relevance_score: float = 0.0


class BrainLayer:
    """
    🧠 Autonomous Website Discovery Engine
    
    Pipeline:
    1. Search Aggregation - Multi-source search
    2. Platform Harvesting - Marketplace scraping
    3. Relevance Filtering - LLM-based scoring
    4. Deduplication - Remove duplicates
    """
    
    def __init__(self):
        self.search_aggregator = SearchAggregator()
        self.platform_harvester = PlatformHarvester()
        self.relevance_filter = RelevanceFilter()
    
    async def discover(
        self,
        query: str,
        max_results: int = 100,
        min_relevance: float = 0.7,
        include_platforms: bool = True
    ) -> list[dict]:
        """
        Discover websites for a given query.
        
        Args:
            query: Search query (e.g., "vintage cameras shop")
            max_results: Maximum number of results to return
            min_relevance: Minimum relevance score (0-1)
            include_platforms: Include platform results (Amazon, eBay, etc.)
        
        Returns:
            List of discovered websites with metadata
        """
        all_results = []
        
        # Phase 1: Search Aggregation
        search_results = await self.search_aggregator.search(
            query, 
            max_results=max_results * 2  # Get extra for filtering
        )
        all_results.extend(search_results)
        
        # Phase 2: Platform Harvesting (optional)
        if include_platforms:
            platform_results = await self.platform_harvester.harvest(query)
            all_results.extend(platform_results)
        
        # Phase 3: Deduplication
        unique_results = self._deduplicate(all_results)
        
        # Phase 4: Relevance Filtering
        if self.relevance_filter.is_available():
            filtered_results = await self.relevance_filter.filter(
                query, 
                unique_results, 
                threshold=min_relevance
            )
        else:
            # Fallback: keyword-based relevance
            filtered_results = self._keyword_filter(query, unique_results)
        
        # Limit to max_results
        return filtered_results[:max_results]
    
    def _deduplicate(self, results: list[dict]) -> list[dict]:
        """Remove duplicate URLs"""
        seen_urls = set()
        unique = []
        
        for result in results:
            url = self._normalize_url(result.get("url", ""))
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(result)
        
        return unique
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        url = url.lower().strip()
        # Remove trailing slash
        if url.endswith("/"):
            url = url[:-1]
        # Remove query params for dedup
        if "?" in url:
            url = url.split("?")[0]
        return url
    
    def _keyword_filter(self, query: str, results: list[dict]) -> list[dict]:
        """Simple keyword-based relevance filter"""
        keywords = query.lower().split()
        scored = []
        
        for result in results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            matches = sum(1 for kw in keywords if kw in text)
            score = matches / len(keywords) if keywords else 0
            result["relevance_score"] = score
            if score > 0.3:
                scored.append(result)
        
        # Sort by relevance
        return sorted(scored, key=lambda x: x.get("relevance_score", 0), reverse=True)


async def main():
    """Test brain layer"""
    brain = BrainLayer()
    results = await brain.discover("vintage cameras shop", max_results=10)
    
    print(f"\n🧠 Discovered {len(results)} websites:\n")
    for r in results:
        print(f"  📌 {r.get('title', 'N/A')[:50]}")
        print(f"     {r.get('url', 'N/A')}")
        print(f"     Score: {r.get('relevance_score', 0):.2f}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
