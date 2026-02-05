"""
Test Script - Run a complete discovery test

Usage: python -m src.test_run "vintage cameras"
"""

import asyncio
import sys
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


async def test_discovery(query: str):
    """Run a complete discovery test"""
    
    console.print(f"\n🧠 [bold blue]Testing Web Scraper[/]\n")
    console.print(f"Query: [green]{query}[/]\n")
    
    # Check configuration
    from src.config import config
    
    table = Table(title="📊 Configuration Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status")
    table.add_column("Details", style="dim")
    
    table.add_row(
        "Serper API",
        "✅" if config.search.serper_api_key else "❌",
        f"{config.search.serper_api_key[:10]}..." if config.search.serper_api_key else "Not configured"
    )
    table.add_row(
        "Groq API",
        "✅" if config.llm.groq_api_key else "❌",
        f"{config.llm.groq_model}" if config.llm.groq_api_key else "Using Ollama"
    )
    
    console.print(table)
    console.print()
    
    # Test Search
    console.print("[bold]1. Testing Search Aggregator...[/]")
    
    from src.brain.search_aggregator import SearchAggregator
    
    aggregator = SearchAggregator()
    try:
        results = await aggregator.search(query, max_results=10)
        console.print(f"   ✅ Found [green]{len(results)}[/] results\n")
        
        if results:
            table = Table(title="🔍 Search Results (Top 5)")
            table.add_column("#", style="dim")
            table.add_column("Title", style="cyan")
            table.add_column("URL", style="blue")
            
            for i, r in enumerate(results[:5], 1):
                table.add_row(
                    str(i),
                    (r.get("title") or "N/A")[:40],
                    (r.get("url") or "N/A")[:50]
                )
            
            console.print(table)
    except Exception as e:
        console.print(f"   ❌ Search failed: {e}\n")
        results = []
    
    # Test Scraping
    if results:
        console.print("\n[bold]2. Testing Scraper...[/]")
        
        from src.scrapers.engine_selector import smart_scrape
        
        test_url = results[0].get("url")
        console.print(f"   URL: {test_url[:60]}...")
        
        try:
            html = await smart_scrape(test_url)
            console.print(f"   ✅ Scraped [green]{len(html)}[/] characters\n")
            
            # Test Email Extraction
            console.print("[bold]3. Testing Email Extractor...[/]")
            from src.extractors.email_extractor import EmailExtractor
            
            emails = EmailExtractor().extract(html)
            console.print(f"   ✅ Found [green]{len(emails)}[/] emails: {emails[:3]}\n")
            
            # Test Social Extraction
            console.print("[bold]4. Testing Social Extractor...[/]")
            from src.extractors.social_extractor import SocialExtractor
            
            social = SocialExtractor().extract(html)
            console.print(f"   ✅ Found social accounts: {list(social.keys())}\n")
            
            # Test LLM Extraction (if Groq configured)
            if config.llm.use_groq:
                console.print("[bold]5. Testing LLM Extractor (Groq)...[/]")
                from src.extractors.llm_extractor import LLMExtractor
                
                extractor = LLMExtractor()
                try:
                    data = await extractor.extract(
                        html, 
                        ["company_name", "email", "phone", "address"]
                    )
                    console.print(f"   ✅ LLM extracted: {data}\n")
                except Exception as e:
                    console.print(f"   ⚠️ LLM extraction: {e}\n")
                finally:
                    await extractor.close()
        
        except Exception as e:
            console.print(f"   ❌ Scraping failed: {e}\n")
    
    console.print("\n[bold green]✅ Test Complete![/]\n")
    
    await aggregator.close()


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "vintage cameras shop"
    asyncio.run(test_discovery(query))
