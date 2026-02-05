# 🧠 Brainstorm: Autonomous Research Engine + Tech Selection

## Context

**Problem:** Build a "brain layer" that autonomously discovers and scrapes websites based on keywords/products. User provides search terms → system finds all relevant websites → scrapes everything (data, emails, social accounts, media).

**Current Gap:** No URL input required; the scraper needs to FIND websites itself.

---

## Part 1: Tech Selection Per Protection Type

### Decision Matrix: Which Tool for Which Firewall?

| Protection | Primary Tool | Fallback | Speed | Reliability |
|------------|--------------|----------|-------|-------------|
| **No Protection** | `httpx` / `aiohttp` | - | ⚡⚡⚡⚡⚡ | 99% |
| **Basic Rate Limit** | `httpx` + delays | Scrapy autothrottle | ⚡⚡⚡⚡ | 95% |
| **Cloudflare Basic** | `curl_cffi` | `cloudscraper` | ⚡⚡⚡⚡ | 90% |
| **Cloudflare Turnstile** | `FlareSolverr` | Playwright + stealth | ⚡⚡ | 85% |
| **Akamai Bot Manager** | `tls_client` + residential | DrissionPage | ⚡⚡ | 70% |
| **PerimeterX** | Residential proxy + Playwright | - | ⚡ | 60% |
| **DataDome** | DrissionPage + human behavior | - | ⚡ | 60% |
| **reCAPTCHA v2** | `2Captcha` API | Playwright + manual | ⚡ | 85% |
| **reCAPTCHA v3** | High-score session | Residential + behavior | ⚡⚡ | 75% |
| **hCaptcha** | `2Captcha` / CapMonster | - | ⚡ | 80% |
| **IP Blocking** | Proxy rotation | Residential pool | ⚡⚡⚡ | 90% |
| **JavaScript Heavy** | Playwright | Splash | ⚡⚡ | 95% |

### Auto-Detection System

```python
async def detect_protection(url: str) -> ProtectionType:
    response = await quick_probe(url)
    
    if "cf-ray" in response.headers:
        return ProtectionType.CLOUDFLARE
    if "akamai" in response.headers.get("server", "").lower():
        return ProtectionType.AKAMAI
    if "_px" in response.cookies:
        return ProtectionType.PERIMETERX
    if "datadome" in str(response.cookies):
        return ProtectionType.DATADOME
    if response.status_code == 429:
        return ProtectionType.RATE_LIMITED
    if len(response.text) < 5000 and "<noscript>" in response.text:
        return ProtectionType.JAVASCRIPT_REQUIRED
    
    return ProtectionType.NONE
```

---

## Part 2: Research Engine / Brain Layer

### Option A: Search Engine Aggregation

**Description:** Use multiple search engines (Google, Bing, DuckDuckGo) to find websites for given keywords.

```
User Input: "vintage cameras shop"
     │
     ▼
┌─────────────────────────────┐
│  Search Engine Aggregator   │
├─────────────────────────────┤
│  • Google (SerpAPI/Serper)  │
│  • Bing API                 │
│  • DuckDuckGo (scrape)      │
│  • Brave Search API         │
└─────────────────────────────┘
     │
     ▼
[1000+ relevant URLs discovered]
```

✅ **Pros:**
- Immediate results from indexed web
- High relevance ranking
- Covers most of the web
- Multiple free tier APIs

❌ **Cons:**
- Limited to indexed pages
- API rate limits (need multi-account)
- May miss deep web / niche sites

📊 **Effort:** Low

**APIs/Tools:**
| Service | Free Tier | Speed |
|---------|-----------|-------|
| SerpAPI | 100 searches/mo | Fast |
| Serper.dev | 2,500 searches/mo | Fast |
| Bing API | 1,000 searches/mo | Fast |
| DuckDuckGo | Scrape (unlimited) | Medium |
| Brave Search | 2,000 searches/mo | Fast |

---

### Option B: Web Graph Exploration (Spider Mode)

**Description:** Start from seed sites and spider outward, discovering related sites via links.

```
User Input: "vintage cameras shop"
     │
     ▼
┌─────────────────────────────┐
│  Seed Discovery             │
│  (Search → top 10 results)  │
└─────────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│  Link Extraction Spider     │
├─────────────────────────────┤
│  • Outbound links           │
│  • Partner/supplier links   │
│  • Directory listings       │
│  • Forum mentions           │
└─────────────────────────────┘
     │
     ▼
[10,000+ URLs via graph traversal]
```

✅ **Pros:**
- Discovers non-indexed sites
- Finds related niche sites
- Unlimited expansion
- No API costs

❌ **Cons:**
- Slower (crawl time)
- May drift off-topic
- Needs relevance filtering
- Higher compute/bandwidth

📊 **Effort:** Medium

---

### Option C: Hybrid Intelligence Layer (Recommended)

**Description:** Combine search aggregation with AI-powered categorization and graph exploration.

```
User Input: "vintage cameras shop"
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    🧠 BRAIN LAYER                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   SEARCH    │    │   SPIDER    │    │    LLM      │    │
│  │  AGGREGATOR │    │   ENGINE    │    │  ANALYZER   │    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    │
│         │                  │                   │           │
│         └──────────────────┼───────────────────┘           │
│                            ▼                               │
│                  ┌─────────────────┐                       │
│                  │  RELEVANCE      │                       │
│                  │  SCORING        │                       │
│                  │  (LLM/ML)       │                       │
│                  └────────┬────────┘                       │
│                           ▼                                │
│                  ┌─────────────────┐                       │
│                  │  URL QUEUE      │                       │
│                  │  (Prioritized)  │                       │
│                  └─────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

✅ **Pros:**
- Best of both worlds
- AI filters irrelevant sites
- Self-expanding discovery
- Learns from patterns
- Can use local LLM (Ollama) for free

❌ **Cons:**
- More complex
- Needs initial tuning
- LLM processing overhead

📊 **Effort:** High (but highest ROI)

---

### Option D: Platform-Specific Harvesters

**Description:** Target specific platforms known to list businesses/products.

```
User Input: "vintage cameras"
     │
     ▼
┌─────────────────────────────────────────────────┐
│  Platform Harvesters                            │
├─────────────────────────────────────────────────┤
│  • E-commerce: Amazon, eBay, Etsy, Shopify      │
│  • Directories: Yelp, YellowPages, Clutch       │
│  • Marketplaces: Alibaba, AliExpress            │
│  • Social: Instagram shops, Facebook pages      │
│  • Forums: Reddit, specialty forums             │
│  • Maps: Google Maps, Apple Maps                │
└─────────────────────────────────────────────────┘
```

✅ **Pros:**
- Structured data
- High-quality listings
- Contact info often available
- Business verified

❌ **Cons:**
- Limited to platforms with listings
- Platform-specific scrapers needed
- Some have strong anti-bot

📊 **Effort:** Medium

---

## Part 3: Recommended Architecture

### 💡 Recommendation: Option C (Hybrid) + Option D (Platforms)

**Why?** Maximum coverage with intelligent filtering:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE BRAIN LAYER                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                        User: "vintage cameras shop"
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │   SEARCH     │ │  PLATFORM    │ │   SOCIAL     │
           │   ENGINES    │ │  HARVESTERS  │ │   SEARCH     │
           │              │ │              │ │              │
           │ • SerpAPI    │ │ • Amazon     │ │ • Instagram  │
           │ • Bing       │ │ • eBay       │ │ • Twitter    │
           │ • DuckDuckGo │ │ • Etsy       │ │ • LinkedIn   │
           │ • Brave      │ │ • Google Maps│ │ • TikTok     │
           └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                  │                │                │
                  └────────────────┼────────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │     LLM RELEVANCE FILTER     │
                    │     (Ollama - Local, Free)   │
                    │                              │
                    │  "Is this about vintage      │
                    │   cameras? Score 0-100"      │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      SPIDER EXPANSION        │
                    │                              │
                    │  High-relevance sites →      │
                    │  Extract outbound links →    │
                    │  Add to queue                │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     PROTECTION DETECTOR      │
                    │     + ENGINE SELECTOR        │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              [curl_cffi]   [Playwright]   [FlareSolverr]
                    │              │              │
                    └──────────────┼──────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │      DATA EXTRACTION         │
                    │  • Emails, phones            │
                    │  • Social links              │
                    │  • Products/services         │
                    │  • Images, videos            │
                    └──────────────────────────────┘
```

---

## Part 4: Questions Before Implementation

1. **Primary use case?**
   - E-commerce competitor analysis?
   - Lead generation (emails/contacts)?
   - Market research?
   - Something else?

2. **Geographic scope?**
   - Global or specific countries?
   - Language preferences?

3. **Data priority?**
   - Contacts (emails/phones) most important?
   - Product catalogs?
   - Social media presence?
   - All equally?

4. **Volume expectation?**
   - How many keywords at once?
   - How many results per keyword (100s? 1000s? 10,000s?)

5. **LLM preference?**
   - Local (Ollama - free, private)?
   - Cloud (OpenAI/Claude - faster, cost)?
   - Hybrid?

---

## What direction would you like to explore?
