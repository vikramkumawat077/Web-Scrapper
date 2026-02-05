"""
Max Speed Web Scraper - Main Entry Point
"""

import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.config import config
from src.brain.brain_layer import BrainLayer
from src.scrapers.engine_selector import smart_scrape
from src.extractors.email_extractor import EmailExtractor
from src.extractors.social_extractor import SocialExtractor

app = typer.Typer(
    name="scraper",
    help="🚀 Max Speed Web Scraper - Autonomous discovery & extraction"
)
console = Console()


@app.command()
def discover(
    query: str = typer.Argument(..., help="Search query for website discovery"),
    max_sites: int = typer.Option(100, "--max-sites", "-m", help="Maximum sites to discover"),
    extract: bool = typer.Option(True, "--extract/--no-extract", help="Extract data from sites"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (JSON)")
):
    """
    🧠 Discover websites for a query and extract data.
    
    Example:
        python -m src.main discover "vintage cameras shop" --max-sites 50
    """
    console.print(f"\n🧠 [bold blue]Brain Layer[/] activated for: [green]{query}[/]\n")
    
    async def run():
        brain = BrainLayer()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Phase 1: Discovery
            task = progress.add_task("Discovering websites...", total=None)
            discovered = await brain.discover(query, max_results=max_sites)
            progress.update(task, completed=True)
            
            console.print(f"✅ Discovered [bold]{len(discovered)}[/] websites\n")
            
            if extract and discovered:
                # Phase 2: Extraction
                task = progress.add_task("Extracting data...", total=len(discovered))
                results = []
                
                for site in discovered:
                    try:
                        html = await smart_scrape(site["url"])
                        emails = EmailExtractor().extract(html)
                        social = SocialExtractor().extract(html)
                        results.append({
                            "url": site["url"],
                            "emails": emails,
                            "social": social
                        })
                    except Exception as e:
                        console.print(f"[yellow]⚠ Failed: {site['url']}: {e}[/]")
                    progress.advance(task)
                
                # Display results
                table = Table(title="📦 Extracted Data")
                table.add_column("URL", style="cyan")
                table.add_column("Emails", style="green")
                table.add_column("Social", style="blue")
                
                for r in results[:20]:  # Show first 20
                    table.add_row(
                        r["url"][:50],
                        ", ".join(r["emails"][:3]),
                        ", ".join([f"{k}: {v}" for k, v in list(r["social"].items())[:2]])
                    )
                
                console.print(table)
                
                # Save if output specified
                if output:
                    import json
                    with open(output, 'w') as f:
                        json.dump(results, f, indent=2)
                    console.print(f"\n💾 Saved to [green]{output}[/]")
                
                return results
        
        return discovered
    
    asyncio.run(run())


@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL to scrape"),
    extract: str = typer.Option("all", "--extract", "-e", help="What to extract: all, emails, social, media"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    ⚡ Scrape a single URL and extract data.
    
    Example:
        python -m src.main scrape "https://example.com" --extract emails
    """
    console.print(f"\n⚡ Scraping: [cyan]{url}[/]\n")
    
    async def run():
        html = await smart_scrape(url)
        
        if verbose:
            console.print(f"[dim]HTML length: {len(html)} chars[/]")
        
        results = {"url": url}
        
        if extract in ["all", "emails"]:
            emails = EmailExtractor().extract(html)
            results["emails"] = emails
            console.print(f"📧 Emails: [green]{emails}[/]")
        
        if extract in ["all", "social"]:
            social = SocialExtractor().extract(html)
            results["social"] = social
            console.print(f"🔗 Social: [blue]{social}[/]")
        
        return results
    
    asyncio.run(run())


@app.command()
def worker(
    concurrency: int = typer.Option(10, "--concurrency", "-c", help="Number of concurrent workers"),
    queue: str = typer.Option("scrape_queue", "--queue", "-q", help="Redis queue name")
):
    """
    🔄 Start a 24/7 worker to process scrape jobs from Redis queue.
    
    Example:
        python -m src.main worker --concurrency 20
    """
    console.print(f"\n🔄 Starting worker with [bold]{concurrency}[/] concurrent tasks\n")
    console.print(f"   Queue: [cyan]{queue}[/]")
    console.print(f"   Redis: [cyan]{config.database.redis_url}[/]\n")
    console.print("[yellow]Press Ctrl+C to stop[/]\n")
    
    # Worker implementation will be in src/worker.py
    from src.worker import run_worker
    asyncio.run(run_worker(concurrency=concurrency, queue_name=queue))


@app.command()
def status():
    """
    📊 Show scraper status and configuration.
    """
    table = Table(title="📊 Configuration Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")
    
    # Check API keys
    table.add_row(
        "Serper API",
        "✅" if config.search.serper_api_key else "❌",
        "Search discovery"
    )
    table.add_row(
        "Bright Data",
        "✅" if config.proxy.bright_data_username else "❌",
        "Premium proxies"
    )
    table.add_row(
        "2Captcha",
        "✅" if config.captcha.twocaptcha_api_key else "❌",
        "CAPTCHA solving"
    )
    table.add_row(
        "Supabase",
        "✅" if config.database.supabase_url else "❌",
        "Database storage"
    )
    table.add_row(
        "Redis",
        "✅" if config.database.redis_url else "❌",
        config.database.redis_url
    )
    
    console.print(table)


if __name__ == "__main__":
    app()
