"""
Relevance Filter - LLM-Based Relevance Scoring

Uses Ollama (local LLM) to score relevance of discovered websites.
"""

import json
from typing import Optional
import httpx
from src.config import config


class RelevanceFilter:
    """
    LLM-powered relevance filtering using Ollama.
    
    Scores each discovered website for relevance to the original query,
    filtering out noise and focusing on high-quality leads.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.model = config.llm.model_name
        self._available = None
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        if self._available is not None:
            return self._available
        
        try:
            import httpx
            response = httpx.get(f"{config.llm.ollama_host}/api/tags", timeout=5.0)
            self._available = response.status_code == 200
        except:
            self._available = False
        
        return self._available
    
    async def filter(
        self, 
        query: str, 
        results: list[dict], 
        threshold: float = 0.7,
        batch_size: int = 10
    ) -> list[dict]:
        """
        Filter results based on relevance to query.
        
        Args:
            query: Original search query
            results: List of discovered websites
            threshold: Minimum relevance score (0-1)
            batch_size: Number of results to score at once
        
        Returns:
            Filtered list of relevant websites
        """
        if not self.is_available():
            return results
        
        scored_results = []
        
        # Process in batches
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            scores = await self._score_batch(query, batch)
            
            for result, score in zip(batch, scores):
                result["relevance_score"] = score
                if score >= threshold:
                    scored_results.append(result)
        
        # Sort by relevance
        return sorted(
            scored_results, 
            key=lambda x: x.get("relevance_score", 0), 
            reverse=True
        )
    
    async def _score_batch(self, query: str, results: list[dict]) -> list[float]:
        """Score a batch of results"""
        prompt = self._build_prompt(query, results)
        
        try:
            response = await self.client.post(
                f"{config.llm.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_scores(data.get("response", ""), len(results))
        except Exception as e:
            print(f"LLM scoring error: {e}")
        
        # Fallback: return neutral scores
        return [0.5] * len(results)
    
    def _build_prompt(self, query: str, results: list[dict]) -> str:
        """Build scoring prompt for LLM"""
        sites = []
        for i, r in enumerate(results):
            sites.append(f"{i+1}. {r.get('title', 'N/A')} - {r.get('url', 'N/A')}")
            if r.get('snippet'):
                sites.append(f"   {r.get('snippet', '')[:100]}")
        
        sites_text = "\n".join(sites)
        
        return f"""You are scoring websites for relevance to a search query.

QUERY: "{query}"

WEBSITES:
{sites_text}

For each website, score its relevance from 0.0 to 1.0:
- 1.0 = Perfectly relevant (exact match to query intent)
- 0.7 = Highly relevant (related to query)
- 0.5 = Somewhat relevant (tangentially related)
- 0.3 = Low relevance (barely related)
- 0.0 = Not relevant (spam, wrong topic)

Return ONLY a JSON object with scores like:
{{"scores": [0.9, 0.7, 0.3, ...]}}

No explanation needed, just the JSON."""

    def _parse_scores(self, response: str, expected_count: int) -> list[float]:
        """Parse scores from LLM response"""
        try:
            # Try to parse JSON
            data = json.loads(response)
            scores = data.get("scores", [])
            
            # Validate and pad if needed
            scores = [float(s) for s in scores]
            while len(scores) < expected_count:
                scores.append(0.5)
            
            return scores[:expected_count]
        except:
            return [0.5] * expected_count
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
