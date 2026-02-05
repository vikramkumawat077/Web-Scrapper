"""
LLM Extractor - AI-Powered Data Extraction

Uses Groq (fast, free) or Ollama (local) for intelligent extraction.
"""

import json
import re
from typing import Optional
import httpx
from src.config import config


class LLMExtractor:
    """
    LLM-powered data extraction using chain-of-thought.
    
    Supports:
    - Groq API (cloud, fast, free tier)
    - Ollama (local, unlimited)
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def extract(
        self, 
        html: str, 
        fields: list[str],
        max_html_length: int = 5000
    ) -> dict:
        """
        Extract structured data from HTML using LLM.
        
        Args:
            html: Raw HTML content
            fields: Fields to extract (e.g., ["company_name", "email", "phone"])
            max_html_length: Maximum HTML characters to send
        
        Returns:
            Dict with extracted fields
        """
        # Truncate HTML to avoid token limits
        html_snippet = html[:max_html_length]
        
        # Build prompt
        prompt = self._build_prompt(html_snippet, fields)
        
        # Try Groq first (faster), then Ollama
        if config.llm.use_groq:
            return await self._extract_groq(prompt)
        else:
            return await self._extract_ollama(prompt)
    
    async def _extract_groq(self, prompt: str) -> dict:
        """Extract using Groq API"""
        try:
            response = await self.client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.llm.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.llm.groq_model,
                    "messages": [
                        {"role": "system", "content": "You are a data extraction expert. Extract structured data from HTML and return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_json(content)
            else:
                print(f"Groq API error: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Groq extraction error: {e}")
            return {}
    
    async def _extract_ollama(self, prompt: str) -> dict:
        """Extract using Ollama (local)"""
        try:
            response = await self.client.post(
                f"{config.llm.ollama_host}/api/generate",
                json={
                    "model": config.llm.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_json(data.get("response", ""))
            return {}
        except Exception as e:
            print(f"Ollama extraction error: {e}")
            return {}
    
    def _build_prompt(self, html: str, fields: list[str]) -> str:
        """Build extraction prompt"""
        fields_str = ", ".join(fields)
        
        return f"""Extract the following fields from this HTML:
FIELDS: {fields_str}

HTML:
{html}

INSTRUCTIONS:
1. Only extract data that is CLEARLY present in the HTML
2. Use null for missing fields
3. Return ONLY a valid JSON object, no explanation

Example output:
{{
    "company_name": "Example Corp",
    "email": "contact@example.com",
    "phone": null
}}

Your JSON:"""

    def _parse_json(self, text: str) -> dict:
        """Safely parse JSON from LLM response"""
        try:
            # Try direct parse
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON in response
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        return {}
    
    async def score_relevance(self, query: str, sites: list[dict]) -> list[dict]:
        """
        Score site relevance using LLM.
        
        Args:
            query: Original search query
            sites: List of sites with title/snippet
        
        Returns:
            Sites with relevance_score added
        """
        if not sites:
            return sites
        
        # Build sites text
        sites_text = "\n".join([
            f"{i+1}. {s.get('title', 'N/A')} - {s.get('snippet', '')[:100]}"
            for i, s in enumerate(sites[:20])  # Limit to 20
        ])
        
        prompt = f"""Score these websites for relevance to the query "{query}".
Rate each from 0.0 (not relevant) to 1.0 (highly relevant).

WEBSITES:
{sites_text}

Return a JSON object with scores:
{{"scores": [0.9, 0.7, 0.3, ...]}}

Only the JSON, no explanation:"""

        # Get scores
        if config.llm.use_groq:
            result = await self._extract_groq(prompt)
        else:
            result = await self._extract_ollama(prompt)
        
        scores = result.get("scores", [])
        
        # Apply scores
        for i, site in enumerate(sites):
            if i < len(scores):
                site["relevance_score"] = float(scores[i])
            else:
                site["relevance_score"] = 0.5
        
        return sorted(sites, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Convenience function
async def extract_with_llm(html: str, fields: list[str]) -> dict:
    """Quick extraction using default extractor"""
    extractor = LLMExtractor()
    try:
        return await extractor.extract(html, fields)
    finally:
        await extractor.close()
