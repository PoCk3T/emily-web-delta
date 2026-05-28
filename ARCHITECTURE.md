# Emily Web Delta — Architecture & Research Document

> **Author:** Lucas Fontaine (CTO/Co-Founder) via Hermes Agent
> **Date:** 2026-05-28
> **Status:** Architecture Document — Firecrawl-Primary
> **Project Name:** emily-web-delta

---

## TABLE OF CONTENTS

1. Executive Summary
2. Problem Statement & Use Cases
3. Competitive Landscape Analysis
4. Why Firecrawl First
5. System Architecture Overview
6. Firecrawl Integration Design
7. Self-Hosted Fallback Design
8. Database Schema Design
9. API Design
10. Frontend Tech Stack
11. Security Architecture
12. Monitoring, Alerting & Notifications
13. Performance & Scalability
14. Extensibility & Plugin System
15. Deployment & DevOps
16. Implementation Roadmap
17. Technology Recommendations Summary
18. Project Structure
19. Key Design Decisions & Rationale
20. Risks & Mitigations
21. Cost Estimates

---

## 1. EXECUTIVE SUMMARY

This document presents the architecture for **Emily Web Delta** — a web-based platform for monitoring configurable URLs, detecting content changes, computing meaningful deltas, and providing a rich UI for browsing diffs and receiving alerts.

**Core architectural decision: Firecrawl Monitoring API as the primary backend.**

Firecrawl's monitoring service handles the heavy lifting — scheduled scraping, content extraction, AI-powered change judging, structured field extraction, and unified diffs. Our product focuses on what Firecrawl doesn't do: multi-tenant team collaboration, custom web UI, advanced analytics, notification routing, and plugin extensibility.

**The self-hosted fallback** (custom polling, readability-lxml extraction, difflib-based diffing) is a secondary path for users who cannot or will not use Firecrawl. It is fully functional but not the primary development focus.

**Recommended stack:**
- **Backend:** Python 3.12+ with FastAPI (async), SQLAlchemy (ORM)
- **Frontend:** React 18+ with TypeScript, Vite, TailwindCSS, diff2html
- **Database:** PostgreSQL 16+ (primary), Redis (cache + rate limiting)
- **Primary Extraction:** Firecrawl Monitoring API (scraping + AI diffing + structured extraction)
- **Fallback Extraction:** Self-hosted polling with Playwright, readability-lxml, difflib
- **Deployment:** Docker Compose (dev), Docker/Kubernetes (prod)

---

## 2. PROBLEM STATEMENT & USE CASES

### Core Problem
Web pages change constantly — prices, stock status, content, layout, terms of service, job listings, news articles, pricing pages, regulatory filings. Users need to know **when** changes happen, **what** changed, and **how significant** the change is.

### Primary Use Cases

1. **Price Monitoring:** Track e-commerce product prices, detect drops, restock alerts
2. **Content Monitoring:** Track news sites, blogs, regulatory pages, terms of service changes
3. **Competitive Intelligence:** Monitor competitor pricing, features, job postings
4. **Compliance Tracking:** Monitor regulatory filings, policy changes, legal updates
5. **Job Market Monitoring:** Track job listings on company career pages
6. **Availability Monitoring:** Track product restocks, event ticket availability
7. **Infrastructure Monitoring:** Monitor status pages, incident reports, SLA changes
8. **Research & Journalism:** Track changes to sources, verify content edits, document timelines

### Key Requirements

- Configurable URL list (add/remove/enable/disable without code changes)
- Configurable polling intervals per URL
- Meaningful diff computation (AI-powered, not just raw HTML comparison)
- Web-based UI for full interaction
- Notification system (email, webhook, Slack, etc.)
- Snapshot history with timeline view
- Delta visualization (side-by-side, unified, semantic, structured)
- Multi-tenant team collaboration
- Change analytics (frequency, trends, anomaly detection)

---

## 3. COMPETITIVE LANDSCAPE ANALYSIS

### 3.1 changedetection.io (31,752 stars, Python, Apache-2.0)

The dominant open-source player. Self-hosted, Docker-based, browser-based UI.

**Strengths:**
- Massive community (31K+ stars, 1800+ forks)
- Docker-first deployment
- Browser-based UI with diff viewer
- Supports JavaScript-rendered pages (via Playwright/Chrome)
- Multiple notification channels (email, webhook, Slack, Discord, Telegram)
- XPath/CSS filter support for extracting specific elements
- Proximity matching algorithm for fuzzy diff
- RSS feed generation
- Active development (updated daily)

**Gaps:**
- Diff quality is limited — primarily text-based line diffing
- No semantic/paragraph-level diffing
- No structured field extraction (price, stock, etc.)
- No AI-powered change judging
- No multi-tenancy or team collaboration
- No API-first design (primarily a single-user tool)
- No pricing tiers or SaaS features
- No advanced analytics (change frequency, uptime, trend analysis)

### 3.2 Firecrawl Monitoring (Commercial SaaS)

The new entrant with AI-powered monitoring.

**Strengths:**
- AI-powered meaningful change judging (LLM evaluates if change matters)
- JSON-mode structured extraction with per-field diffs
- Mixed mode (JSON + git-diff)
- Crawl monitors (auto-discover and diff all pages)
- Natural language scheduling ("every 30 minutes")
- Webhook-first notifications
- Clean API with Python/JS SDKs
- Credit-based pricing (pay per scrape + per judged change)

**Gaps:**
- No web UI (API-only)
- No multi-tenancy
- No team collaboration
- No self-hosting option
- Vendor lock-in (credit costs, data on their servers)
- No change analytics (frequency, trends, anomaly detection)
- No browser extension
- No plugin system for custom integrations

### 3.3 ArchiveBox (27,562 stars, Python, MIT)

Web archiving tool — saves complete page snapshots.

**Strengths:**
- Comprehensive archiving (HTML, PDF, screenshots, media)
- Supports bookmarks, Pinboard, Pocket, browser history import
- Docker-based, self-hosted
- Rich export options (WARC, singlefile)

**Gaps:**
- Not designed for change detection
- No diff computation between snapshots
- No alerting/notification system
- No structured change tracking
- Overkill for monitoring use case

### 3.4 Visualping (Commercial SaaS)

The leading commercial web monitoring service.

**Strengths:**
- Excellent visual diff (screenshot-based comparison)
- Smart change detection (ignores ads, navigation, timestamps)
- Email/webhook notifications
- API access
- Trusted brand, enterprise customers

**Gaps:**
- Paid service (not free/open-source)
- Limited free tier
- No self-hosted option
- Limited customization
- No semantic diffing or structured data extraction
- No team collaboration features in lower tiers

### 3.5 Distill.io (Commercial SaaS)

Enterprise-focused web monitoring with advanced features.

**Strengths:**
- Enterprise-grade features
- Advanced filtering
- API access
- Team collaboration

**Gaps:**
- Expensive (enterprise pricing)
- No self-hosted option
- Complex setup

### 3.6 Market Gap Analysis

| Feature | changedetection.io | Firecrawl | Visualping | Distill | Emily Web Delta |
|---------|-------------------|-----------|------------|---------|-----------------|
| Self-hosted | Yes | No | No | No | Yes |
| Open-source | Yes | No | No | No | Yes |
| Free tier | Yes (full) | Credit-based | Limited | No | Yes |
| AI judging | No | Yes | Partial | Partial | Yes (via Firecrawl) |
| Structured extraction | No | Yes | No | No | Yes |
| Multi-tenancy | No | No | Yes | Yes | Yes |
| Team collaboration | No | No | Yes | Yes | Yes |
| Web UI | Yes | No | Yes | Yes | Yes |
| API-first | Partial | Yes | Yes | Yes | Yes |
| Plugin system | No | No | No | No | Yes |
| Change analytics | No | No | No | Limited | Yes |
| Browser extension | No | No | Yes | No | Future |
| Mobile app | No | No | No | No | Future |

**Key Differentiators for Emily Web Delta:**
1. **Web UI + multi-tenant SaaS** — Firecrawl has no UI, no teams, no plans
2. **Change analytics** — frequency analysis, trend detection, anomaly alerts
3. **Plugin system** — extensible parsers, diff engines, notification channels
4. **Self-hosting option** — for air-gapped, on-premise, or cost-sensitive users
5. **Unified platform** — one place for all monitoring needs, not just API

---

## 4. WHY FIRECRAWL FIRST

### 4.1 What Firecrawl Solves

| Problem | Self-Built | Firecrawl |
|---------|-----------|-----------|
| Reliable scraping | Months of work, edge cases | Production-ready, handles JS, cookies, headers |
| Content extraction | readability-lxml + trafilatura + custom rules | AI-powered, handles any page structure |
| Change judging | Heuristic rules, false positives | LLM judges if change matters, returns confidence + reason |
| Structured extraction | Custom schema parsing | JSON-mode with Pydantic/zod schemas, per-field diffs |
| Crawl discovery | Custom crawler | Auto-discovers all pages, diffs each one |
| Diff quality | Line-level, noisy | Unified text diff + JSON diff + AI summary |
| Infrastructure | Self-managed, scaling headaches | Managed, scales with usage |

### 4.2 Development Time Savings

| Component | Self-Built | With Firecrawl |
|-----------|-----------|----------------|
| Scraping engine | 2-3 weeks | 0 days (API) |
| Content extraction | 1-2 weeks | 0 days (API) |
| Diff engine | 1-2 weeks | 0 days (API) |
| AI change judging | 2-3 weeks | 0 days (API) |
| Crawl discovery | 1-2 weeks | 0 days (API) |
| Notification system | 1 week | 1 week (our job) |
| Web UI | 3-4 weeks | 3-4 weeks (our job) |
| Multi-tenancy | 2 weeks | 2 weeks (our job) |
| Change analytics | 2 weeks | 2 weeks (our job) |
| **Total** | **10-15 weeks** | **8-10 weeks** |

**Net savings: ~40% development time, 4-5 weeks faster to market.**

### 4.3 Quality Advantage

Firecrawl's AI judging is genuinely novel and hard to replicate:

- You pass a plain-language `goal`: "Alert when a new Hacker News story related to AI enters the top 10"
- The LLM judges each change against that goal
- Returns `meaningful`, `confidence`, `reason`, `meaningfulChanges`
- Suppresses noise automatically

This is what we planned to build with semantic diffing, but Firecrawl has it production-ready with an LLM.

### 4.4 Cost Trade-off

| Scenario | Self-Built | Firecrawl |
|----------|-----------|-----------|
| 100 URLs, 5 min interval, 30 days | $0 (self-hosted) | ~$14,400 credits (100 x 2880 checks) |
| 100 URLs, 30 min interval, 30 days | $0 (self-hosted) | ~$2,880 credits |
| 100 URLs, hourly, 30 days | $0 (self-hosted) | ~$21,600 credits |
| 10 URLs, daily, 30 days | $0 (self-hosted) | ~$288 credits |

**Key insight:** Firecrawl costs scale with frequency. For high-frequency monitoring (5 min intervals), costs can be significant. For daily/low-frequency monitoring, costs are negligible.

**Mitigation:** Self-hosted fallback for high-frequency monitoring where cost is a concern. Users can mix: Firecrawl for daily/low-frequency, self-hosted for high-frequency.

---

## 5. SYSTEM ARCHITECTURE OVERVIEW

### 5.1 High-Level Component Diagram

```
+------------------------------------------------------------------+
|                        CLIENT LAYER                               |
|  +----------+  +----------+  +---------------------------------+  |
|  | Web UI   |  | Mobile   |  |  External API / CLI Clients     |  |
|  | (React)  |  | (Future) |  |  (Third-party integrations)     |  |
|  +----+-----+  +----------+  +--------------+------------------+  |
|       |                                    |                      |
+-------+------------------------------------+----------------------+
        |                                    |
        |  HTTPS (JSON API + SPA)           |
        |                                    |
+-------+------------------------------------+----------------------+
|       |           API GATEWAY / LB          |                      |
|       |     (Nginx / Cloudflare / ALB)      |                      |
|       +-------------------+-----------------+                      |
|                           |                                        |
+---------------------------+----------------------------------------+
|                           |           SERVICE LAYER                 |
|  +------------------------+----------------------------------------+|
|  |     FastAPI Server (Monolith Modules)                           |
|  |  +----------+ +----------+ +----------+ +--------------------+  |
|  |  | Auth     | | URL CRUD | | Diff     | | Notification       |  |
|  |  | Service  | | Service  | | Engine   | | Service            |  |
|  |  +----------+ +----------+ +----------+ +--------------------+  |
|  |  +----------+ +----------+ +----------+ +--------------------+  |
|  |  | Config   | | Health   | | Admin    | | Plugin System      |  |
|  |  | Service  | | Service  | | Service  | |                    |  |
|  |  +----------+ +----------+ +----------+ +--------------------+  |
|  +---------------------------------------------------------------+|
|                           |                                        |
+---------------------------+----------------------------------------+
|                           |         BACKEND LAYER                  |
|  +------------------------+----------------------------------------+|
|  |  Primary: Firecrawl Monitoring API                             ||
|  |  - Scheduled scraping                                        ||
|  |  - AI-powered change judging                                 ||
|  |  - JSON-mode structured extraction                           ||
|  |  - Crawl monitors                                            ||
|  |  - Webhook delivery                                          ||
|  +---------------------------------------------------------------+|
|  |  Fallback: Self-Hosted Polling Engine                        ||
|  |  - Celery workers for polling                                ||
|  |  - Playwright for JS rendering                               ||
|  |  - readability-lxml + trafilatura for extraction             ||
|  |  - difflib + custom semantic for diffing                     ||
|  +---------------------------------------------------------------+|
|                           |                                        |
+---------------------------+----------------------------------------+
|                           |         DATA LAYER                     |
|  +------------------------+----------------------------------------+|
|  |  PostgreSQL  ------  |  ------  Redis                          ||
|  |  (URLs, Snapshots,  |  (Rate limit counters,                   ||
|  |   Users, Configs)   |   Cache, Session storage)               ||
|  +------------------------+----------------------------------------+|
|  |  Object Storage (S3/  |  ------  Log Aggregation               ||
|  |  MinIO)               |  ------  (Prometheus + Grafana)        ||
|  +------------------------+----------------------------------------+|
+------------------------------------------------------------------+
```

### 5.2 Data Flow

```
1. PRIMARY PATH (Firecrawl):
   User creates monitor via Web UI
        |
        v
   FastAPI Server -> Firecrawl API (POST /v2/monitor)
        |
        v
   Firecrawl handles:
   - Scheduling (cron/natural language)
   - Scraping (with JS rendering, cookies, headers)
   - Content extraction (AI-powered)
   - Change detection (hash comparison)
   - Diff computation (text + JSON + AI judging)
   - Webhook delivery (monitor.page, monitor.check.completed)
        |
        v
   Our backend receives webhooks -> stores in PostgreSQL
        |
        v
   Web UI polls API -> displays diffs, notifications, analytics

2. FALLBACK PATH (Self-Hosted):
   User creates monitor via Web UI
        |
        v
   FastAPI Server -> stores config in PostgreSQL
        |
        v
   Celery Beat -> polls URLs on schedule
        |
        v
   Celery Workers:
   - Fetch URL (Playwright for JS, httpx for static)
   - Extract content (readability-lxml, trafilatura)
   - Compute diff (difflib, semantic extraction)
   - Store snapshot + diff in PostgreSQL
        |
        v
   Notification Service -> email/webhook/Slack
        |
        v
   Web UI polls API -> displays diffs, notifications, analytics
```

### 5.3 Firecrawl vs Self-Hosted Decision Matrix

| Criterion | Firecrawl (Primary) | Self-Hosted (Fallback) |
|-----------|-------------------|----------------------|
| Development speed | Fast (API integration) | Slow (custom engine) |
| Diff quality | Excellent (AI judging) | Good (heuristic rules) |
| Structured extraction | Excellent (JSON-mode) | Good (custom schemas) |
| Cost at scale | Credit-based ($0.01-0.05/scrape) | Infrastructure-only |
| Self-hosting | No | Yes |
| Vendor lock-in | High | None |
| Customization | Limited (API constraints) | Full control |
| Air-gapped/on-prem | No | Yes |
| Maintenance | None (managed service) | High (self-managed) |
| Best for | Most users, low/medium frequency | High-frequency, cost-sensitive, air-gapped |

---

## 6. FIRECRAWL INTEGRATION DESIGN

### 6.1 API Integration Points

```python
# Primary endpoints we integrate with:

# 1. Create monitor (scrape or crawl)
POST /v2/monitor
Body: {
    "name": "Monitor Name",
    "schedule": {"cron": "*/30 * * * *", "timezone": "UTC"},
    "goal": "Alert when price changes",  # AI judging prompt
    "targets": [{
        "type": "scrape",  # or "crawl"
        "urls": ["https://example.com/pricing"],
        "scrapeOptions": {
            "formats": ["markdown"],  # or ["json"] for structured
            "maxAge": 0
        }
    }],
    "notification": {
        "email": {"enabled": True, "recipients": [...]}
    }
}

# 2. List monitors
GET /v2/monitor

# 3. Get monitor details
GET /v2/monitor/{monitorId}

# 4. Update monitor
PUT /v2/monitor/{monitorId}

# 5. Delete monitor
DELETE /v2/monitor/{monitorId}

# 6. List checks
GET /v2/monitor/{monitorId}/checks?limit=25&status=changed

# 7. Get check details
GET /v2/monitor/{monitorId}/checks/{checkId}

# 8. Run monitor immediately
POST /v2/monitor/{monitorId}/run
```

### 6.2 Webhook Integration

Firecrawl sends two webhook events:

```python
# Event 1: monitor.page (per-page, as each scrape finishes)
{
    "success": True,
    "type": "monitor.page",
    "data": [{
        "monitorId": "...",
        "checkId": "...",
        "url": "https://example.com/pricing",
        "status": "changed",  # same, new, changed, removed, error
        "isMeaningful": True,
        "judgment": {
            "meaningful": True,
            "confidence": "high",
            "reason": "The Starter plan price changed.",
            "meaningfulChanges": [...]
        },
        "diff": {
            "text": "--- previous\n+++ current\n...",
            "json": {"plans[0].price": {"previous": "$19/mo", "current": "$24/mo"}}
        },
        "snapshot": {"json": {...}}
    }]
}

# Event 2: monitor.check.completed (after full check reconciled)
{
    "success": True,
    "type": "monitor.check.completed",
    "data": [{
        "monitorId": "...",
        "checkId": "...",
        "status": "completed",
        "summary": {
            "totalPages": 2,
            "same": 1,
            "changed": 1,
            "new": 0,
            "removed": 0,
            "error": 0
        }
    }]
}
```

### 6.3 Our Webhook Handler

```python
# app/api/webhooks.py

@app.post("/api/v1/webhooks/firecrawl")
async def firecrawl_webhook(request: Request):
    """Receive and process Firecrawl monitor webhooks."""
    payload = await request.json()
    event_type = payload.get("type")
    
    if event_type == "monitor.page":
        for page in payload["data"]:
            await store_check_result(page)
            await trigger_notifications(page)
    
    elif event_type == "monitor.check.completed":
        for check in payload["data"]:
            await store_check_summary(check)
            await trigger_notifications(check)
    
    return {"success": True}
```

### 6.4 Firecrawl Monitor Model

```python
# app/models/firecrawl_monitor.py

class FirecrawlMonitor(BaseModel):
    """Maps our internal monitor to Firecrawl's monitor."""
    id: UUID
    firecrawl_monitor_id: str  # Firecrawl's monitor ID
    name: str
    url: str
    interval_seconds: int
    enabled: bool
    schedule_type: str  # "firecrawl" or "selfhosted"
    firecrawl_config: JSONB  # Raw Firecrawl API config
    last_check_id: str
    last_check_at: datetime
    estimated_credits_per_month: int
    
    # Computed fields
    total_checks: int
    total_changes: int
    last_change_at: datetime
```

---

## 7. SELF-HOSTED FALLBACK DESIGN

### 7.1 When to Use Self-Hosted

The self-hosted fallback is for:
- High-frequency monitoring (5 min intervals) where Firecrawl credits are cost-prohibitive
- Air-gapped or on-premise deployments where external API calls are not allowed
- Users who want full control over extraction, diffing, and storage
- Cost-sensitive deployments where credit-based pricing is unsustainable

### 7.2 Self-Hosted Pipeline

```
+----------------------------------------------------------+
|                 SCHEDULER (Main Process)                    |
|  APScheduler: runs every 10 seconds                        |
|  - Queries DB for URLs where next_check <= NOW()           |
|  - Batches URLs into chunks (max 50 per batch)             |
|  - Publishes tasks to Celery queue                          |
+----------------------------------------------------------+
                          |
                          v
+----------------------------------------------------------+
|              CELERY QUEUE (Redis)                           |
|  url_poll: {url_id, tenant_id, attempt}                   |
|  url_diff: {snapshot_from_id, snapshot_to_id}             |
|  url_notify: {diff_id, tenant_id, rules}                  |
+----------------------------------------------------------+
                          |
          +---------------+---------------+
          v               v               v
   +----------+  +----------+  +----------+
   | Worker 1 |  | Worker 2 |  | Worker N |
   | (poll)   |  | (poll)   |  | (poll)   |
   +----------+  +----------+  +----------+

Each worker:
  1. Fetch URL (Playwright for JS, httpx for static)
  2. Extract content (readability-lxml, trafilatura)
  3. Compute hash (SHA-256 of normalized text)
  4. Compare with last_hash
  5. If changed: compute diff (difflib, semantic)
  6. Store snapshot + diff in PostgreSQL
  7. Trigger notifications
```

### 7.3 Self-Hosted Components

```python
# app/workers/polling.py
async def poll_url(url_id: UUID):
    """Fetch URL, extract content, compute diff."""
    url = await get_url(url_id)
    
    # Step 1: Fetch
    if url.js_required:
        content = await fetch_with_playwright(url.url, url.headers)
    else:
        content = await fetch_with_httpx(url.url, url.headers)
    
    # Step 2: Extract
    extracted = await extract_content(content, url.extraction_method)
    
    # Step 3: Hash
    content_hash = hashlib.sha256(extracted.encode()).hexdigest()
    
    # Step 4: Compare
    if content_hash == url.last_hash:
        return  # No change
    
    # Step 5: Diff
    previous_snapshot = await get_latest_snapshot(url_id)
    diff = await compute_diff(previous_snapshot.extracted_text, extracted)
    
    # Step 6: Store
    await store_snapshot(url_id, content, extracted, content_hash)
    await store_diff(url_id, previous_snapshot.id, diff)
    
    # Step 7: Notify
    await trigger_notifications(url_id, diff)
```

### 7.4 Extraction Methods

| Method | Library | Best For |
|--------|---------|----------|
| readability-lxml | Mozilla's Readability | Articles, blogs, news |
| trafilatura | Multi-language | Multilingual sites, structured content |
| custom XPath | lxml | Targeted element extraction |
| JSON path | jsonpath-ng | API responses, structured data |

### 7.5 Diff Engine

```python
# app/core/diff_engine.py

async def compute_diff(previous_text: str, current_text: str) -> DiffResult:
    """Compute diff between two text snapshots."""
    
    # Line-level diff
    line_diff = difflib.unified_diff(
        previous_text.splitlines(),
        current_text.splitlines(),
        lineterm=""
    )
    
    # Semantic extraction (prices, dates, stock levels)
    semantic_changes = await extract_semantic_changes(previous_text, current_text)
    
    return DiffResult(
        unified_diff="\n".join(line_diff),
        semantic_changes=semantic_changes,
        lines_added=len([l for l in line_diff if l.startswith("+")]),
        lines_removed=len([l for l in line_diff if l.startswith("-")]),
    )
```

---

## 8. DATABASE SCHEMA DESIGN

### 8.1 Entity Relationship Diagram

```
+--------------+       +--------------+       +------------------+
|    users     |       |   tenants    |       |    api_keys      |
+--------------+       +--------------+       +------------------+
| id (PK)      |1    n| id (PK)      |1    n| id (PK)          |
| email        |-------| name         |-------| tenant_id (FK)   |
| password_hash|       | plan         |       | key_hash         |
| is_active    |       | max_urls     |       | prefix           |
| created_at   |       | created_at   |       | created_at       |
+--------------+       +--------------+       +------------------+

+--------------+       +------------------+
|    urls      |       |  url_snapshots   |
+--------------+       +------------------+
| id (PK)      |1    n| id (PK)          |
| tenant_id(FK)|-------| url_id (FK)      |
| name         |       | content_hash     |
| url          |       | content          |  <- raw HTML (S3) or text
| interval_sec |       | extracted_text   |  <- cleaned text
| enabled      |       | content_type     |
| last_checked |       | status           |
| last_hash    |       | created_at       |
| next_check   |       | snapshot_size    |
| headers      |       | diff_from_prev   |  <- JSON diff
| cookies      |       +------------------+
| js_required  |       1    n
| max_retries  |       +------------------+
| user_agent   |       |  url_diffs       |
| backend      |       +------------------+
+--------------+       +------------------+
                       +------------------+
                       | id (PK)          |
                       | snapshot_from(FK)|
                       | snapshot_to (FK) |
                       | diff_type        |  <- unified|semantic|json
                       | diff_content     |  <- JSON
                       | diff_size        |
                       | created_at       |
                       +------------------+

+------------------+       +------------------+
|  url_config      |       |  notifications   |
+------------------+       +------------------+
| id (PK)          |       | id (PK)          |
| url_id (FK)      |       | url_id (FK)      |
| key              |       | tenant_id (FK)   |
| value            |       | type             |  <- email|webhook|slack
+------------------+       | channel          |
                           | enabled          |
                           | config (JSON)    |
                           | last_sent_at     |
                           +------------------+

+------------------+       +------------------+
|  change_alerts   |       |    audit_log     |
+------------------+       +------------------+
| id (PK)          |       | id (PK)          |
| url_id (FK)      |       | tenant_id (FK)   |
| snapshot_id (FK) |       | user_id (FK)     |
| alert_type       |       | action           |
| sent             |       | resource_type    |
| sent_at          |       | resource_id      |
+------------------+       | details (JSON)   |
                           | created_at       |
                           +------------------+
```

### 8.2 Key Table Additions for Firecrawl

```sql
-- URLs table (added backend column)
ALTER TABLE urls ADD COLUMN backend VARCHAR(20) DEFAULT 'firecrawl';
-- Values: 'firecrawl' (primary), 'selfhosted' (fallback)

-- Firecrawl monitor mapping
CREATE TABLE firecrawl_monitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    url_id UUID REFERENCES urls(id) ON DELETE CASCADE,
    firecrawl_monitor_id VARCHAR(100) NOT NULL,  -- Firecrawl's ID
    firecrawl_config JSONB NOT NULL,              -- Raw API config
    status VARCHAR(20) DEFAULT 'active',          -- active, paused, error
    last_check_id VARCHAR(100),
    last_check_at TIMESTAMPTZ,
    estimated_credits_per_month INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(firecrawl_monitor_id)
);

-- Check results (from Firecrawl webhooks or self-hosted polling)
CREATE TABLE check_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_id UUID REFERENCES urls(id) ON DELETE CASCADE,
    check_id VARCHAR(100),  -- Firecrawl check ID or local ID
    backend VARCHAR(20) DEFAULT 'firecrawl',
    status VARCHAR(20) DEFAULT 'completed',  -- same, changed, new, removed, error
    is_meaningful BOOLEAN,  -- Firecrawl AI judgment
    judgment JSONB,  -- Firecrawl judgment: {meaningful, confidence, reason, meaningfulChanges}
    diff_text TEXT,  -- Unified diff
    diff_json JSONB,  -- JSON-mode diff
    diff_size INT,
    snapshot_json JSONB,  -- Snapshot data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_results_url_status (url_id, created_at DESC)
);
```

### 8.3 Storage Strategy

```
Decision: Store diff results in PostgreSQL, raw HTML in S3/MinIO.

Storage hierarchy:
+-- check_results.diff_text -> PostgreSQL TEXT (unified diff)
+-- check_results.diff_json -> PostgreSQL JSONB (JSON-mode diff)
+-- check_results.snapshot_json -> PostgreSQL JSONB (snapshot data)
+-- url_snapshots.content -> S3/MinIO (raw HTML, compressed)
+-- url_snapshots.extracted_text -> PostgreSQL TEXT (cleaned text)
```

---

## 9. API DESIGN

### 9.1 RESTful API Endpoints

```
BASE: /api/v1

=== AUTHENTICATION ===
POST   /auth/register              # Create account
POST   /auth/login                 # Email/password
POST   /auth/logout                # Invalidate session
POST   /auth/refresh               # Refresh JWT
POST   /auth/forgot-password       # Request password reset
POST   /auth/reset-password        # Reset with token
GET    /auth/me                    # Current user profile

=== TENANT MANAGEMENT ===
GET    /tenants                    # List tenants (admin)
GET    /tenants/:id                # Get tenant
PUT    /tenants/:id                # Update tenant
DELETE /tenants/:id                # Delete tenant (admin)

=== API KEYS ===
POST   /api-keys                   # Create API key
GET    /api-keys                   # List API keys
DELETE /api-keys/:id               # Revoke API key

=== URL MANAGEMENT (CRUD) ===
POST   /urls                       # Create new URL to monitor
GET    /urls                       # List all URLs (with pagination, filtering)
GET    /urls/:id                   # Get URL details
PUT    /urls/:id                   # Update URL config
DELETE /urls/:id                   # Delete URL
PATCH  /urls/:id/enable            # Enable monitoring
PATCH  /urls/:id/disable           # Disable monitoring
POST   /urls/:id/check-now         # Trigger immediate check
GET    /urls/:id/health            # URL health status

=== CHECKS (unified across Firecrawl + self-hosted) ===
GET    /urls/:id/checks            # List checks (paginated, filterable)
GET    /urls/:id/checks/:check_id  # Get check details
GET    /urls/:id/checks/:check_id/diff  # Get rendered diff

=== DIFFS ===
GET    /urls/:id/diffs             # List diffs
GET    /urls/:id/diffs/:id         # Get specific diff
GET    /urls/:id/diffs/:id/rendered  # Get rendered HTML diff
GET    /urls/:id/diffs/:id/download  # Download diff as HTML/JSON

=== NOTIFICATIONS ===
POST   /notifications/rules       # Create notification rule
GET    /notifications/rules       # List notification rules
PUT    /notifications/rules/:id   # Update notification rule
DELETE /notifications/rules/:id   # Delete notification rule
POST   /notifications/rules/:id/test  # Test notification

=== ADMIN ===
GET    /admin/health               # System health check
GET    /admin/stats                # Platform statistics
GET    /admin/urls-overview        # All URLs status overview
GET    /admin/worker-status        # Celery worker health (self-hosted only)
GET    /admin/config               # System configuration
PUT    /admin/config               # Update system configuration
GET    /admin/audit-log            # Audit log (admin)

=== ANALYTICS ===
GET    /urls/:id/analytics         # Change frequency, trends, anomalies
GET    /urls/analytics             # Platform-wide analytics
GET    /urls/analytics/export      # Export analytics data

=== WEBHOOKS ===
POST   /webhooks/firecrawl         # Firecrawl webhook endpoint
POST   /webhooks/:id               # Trigger webhook (admin)
GET    /webhooks/:id/logs          # Webhook delivery logs

=== EXPORT ===
GET    /urls/:id/export            # Export all snapshots/diffs
GET    /urls/export                # Bulk export (all URLs)
```

### 9.2 Request/Response Examples

```json
// POST /api/v1/urls
// Request:
{
  "name": "Amazon Product Page",
  "url": "https://www.amazon.com/dp/B08N5WRWNW",
  "interval_seconds": 300,
  "enabled": true,
  "backend": "firecrawl",  // or "selfhosted"
  "firecrawl_config": {
    "goal": "Alert when price or stock status changes",
    "schedule": {"text": "every 5 minutes", "timezone": "UTC"},
    "scrapeOptions": {
      "formats": ["markdown"]
    }
  },
  "tags": ["price-tracking", "amazon"],
  "notification_rules": [
    {
      "type": "email",
      "channel": "alerts@example.com",
      "enabled": true
    }
  ]
}

// Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Amazon Product Page",
  "url": "https://www.amazon.com/dp/B08N5WRWNW",
  "interval_seconds": 300,
  "enabled": true,
  "backend": "firecrawl",
  "last_checked": null,
  "last_hash": null,
  "next_check": "2026-05-28T12:00:00Z",
  "tags": ["price-tracking", "amazon"],
  "status": "active",
  "created_at": "2026-05-28T11:55:00Z",
  "snapshot_count": 0,
  "firecrawl_monitor_id": "019df960-06e7-7383-9d89-82c0113dc31a",
  "notification_rules": [...]
}

// GET /api/v1/urls/:id/checks
// Response (200 OK):
{
  "data": [
    {
      "id": "check-001",
      "check_id": "019df960-5f2a-75fb-a98b-bd2d32ca67d4",
      "backend": "firecrawl",
      "status": "changed",
      "is_meaningful": true,
      "judgment": {
        "meaningful": true,
        "confidence": "high",
        "reason": "The Starter plan price changed."
      },
      "diff_size": 5,
      "created_at": "2026-05-28T12:05:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

## 10. FRONTEND TECH STACK

### 10.1 Recommended Stack

**React 18+ + TypeScript + Vite + diff2html + TailwindCSS**

Justification:
1. **diff2html** provides unified and side-by-side diff views
2. **monaco-editor** as an alternative view mode for code-heavy diffs
3. **TailwindCSS** for rapid, consistent styling
4. **Zustand** for state management or **TanStack Query** for server state caching
5. **React Router v6** for routing

### 10.2 Key UI Components

```
+----------------------------------------------------------+
|  URL: example.com/product-page                           |
|  Last checked: 2 min ago  |  Interval: 5 min  |  [Refresh]|
+----------------------------------------------------------+
|  [Unified] [Side-by-Side] [JSON] [AI Summary]            |
+----------------------------------------------------------+
|  +----------------------------------------------------+  |
|  |  <del>- Price: $19.99                            </del>|
|  |  <ins>+ Price: $14.99                            </ins>|
|  |  <del>- Stock: In Stock                          </del>|
|  |  <ins>+ Stock: Out of Stock                      </ins>|
|  +----------------------------------------------------+  |
+----------------------------------------------------------+
|  +----------------------------------------------------+  |
|  |  AI Judgment (Firecrawl)                           |  |
|  |  Meaningful: Yes (confidence: high)                |  |
|  |  Reason: The Starter plan price changed.            |  |
|  +----------------------------------------------------+  |
+----------------------------------------------------------+
|  [Snapshot Timeline]                                     |
|  O---O---O---O---O---O---O---O---O---O                    |
|  Jan Feb Mar Apr May Jun Jul Aug Sep Oct                 |
+----------------------------------------------------------+
|  [Change Analytics]                                      |
|  Frequency: 12 changes/month (avg)                       |
|  Trend: Price decreasing (-$5.00 over 30 days)           |
|  Anomaly: 3x more changes than usual (last 24h)          |
+----------------------------------------------------------+
```

---

## 11. SECURITY ARCHITECTURE

### 11.1 Threat Model

| Threat | Mitigation |
|--------|-----------|
| XSS via stored HTML | Sanitize all HTML before rendering, use CSP headers, use DOMPurify on frontend |
| Data exfiltration | Tenant isolation at DB level (tenant_id FK), Row-level security policies, API key scoping |
| DDoS / abuse | Rate limiting (Redis-based sliding window), Cloudflare/WAF in front, Request size limits |
| SQL injection | Parameterized queries (SQLAlchemy ORM), Input validation (Pydantic models), WAF rules |
| Credential theft | bcrypt/argon2 password hashing, JWT RS256, API key rotation, Audit logging |
| Unauthorized access | RBAC (tenant admin, member, read-only), Tenant ID on every query, CORS restrictions |
| Content injection | Validate URL scheme (http/https only), Block internal IPs (127.0.0.1, 10.x.x.x), URL allowlist for enterprise |
| Firecrawl API key leak | Store encrypted in DB, never log, rotate automatically |

---

## 12. MONITORING, ALERTING & NOTIFICATIONS

### 12.1 Notification Channels

| Channel | Implementation | Details |
|---------|---------------|---------|
| Email | SMTP (SendGrid, AWS SES, Mailgun) | HTML + plain text diffs, configurable from/to, templates |
| Webhook | HTTP POST to arbitrary URL | JSON payload with diff summary, Retry with exponential backoff |
| Slack | Slack API (Incoming Webhook / Bot) | Rich message with diff preview, Thread per URL |
| Telegram | Telegram Bot API | Markdown-formatted diffs, Per-chat configuration |
| Discord | Discord Webhook | Embed format with diff preview |
| Push (Future) | Firebase Cloud Messaging | Mobile push notifications |

### 12.2 Notification Rules

```json
{
  "notification_rules": {
    "min_diff_size": 5,
    "cooldown_seconds": 300,
    "max_notifications_per_day": 50,
    "significant_only": true,  // Only notify for meaningful changes (Firecrawl)
    "diff_thresholds": {
      "warning": 100,
      "critical": 500
    }
  }
}
```

---

## 13. PERFORMANCE & SCALABILITY

### 13.1 Scaling Strategy

| Phase | URLs | Architecture | Cost |
|-------|------|-------------|------|
| Phase 1 | 0-100 | Single FastAPI + PostgreSQL on same host | ~$10/month (VPS) + Firecrawl credits |
| Phase 2 | 100-1000 | 2 FastAPI instances behind LB, Managed PostgreSQL | ~$50-100/month + Firecrawl credits |
| Phase 3 | 1000-10000 | Kubernetes cluster, PostgreSQL read replicas, S3 | ~$500-1000/month + Firecrawl credits |
| Phase 4 | 10000+ | Microservices decomposition, Multi-region | ~$2000+/month + Firecrawl credits |

### 13.2 Storage Growth Management

```
Pruning Strategy:
+----------------------------------------------------------+
| Per URL:                                                  |
|   - Keep last N snapshots (configurable, default: 30)     |
|   - Keep last M diffs (configurable, default: 10)         |
|   - Archive old snapshots to cold storage (S3 Glacier)    |
|                                                           |
| Storage Estimation:                                       |
|   Average diff: 5KB (JSON + text)                         |
|   100 URLs x 30 snapshots x 5KB = 15MB                    |
|   1000 URLs x 30 snapshots x 5KB = 150MB                  |
|   10000 URLs x 30 snapshots x 5KB = 1.5GB                 |
+----------------------------------------------------------+
```

---

## 14. EXTENSIBILITY & PLUGIN SYSTEM

### 14.1 Plugin Architecture

```
+----------------------------------------------------------+
|                  PLUGIN ARCHITECTURE                        |
|                                                           |
|  +----------------------------------------------------+  |
|  |              Plugin Registry                       |  |
|  |  - Discovers plugins from entry points             |  |
|  |  - Validates plugin interfaces                     |  |
|  |  - Manages plugin lifecycle                        |  |
|  +----------------+-----------------------------------+  |
|                   |                                      |
|    +--------------+--------------+--------------+        |
|    v              v              v              v         |
|  +------+  +--------+  +----------+  +-----------+       |
|  | HTML |  | Diff   |  | Notify   |  | URL      |       |
|  | Parser|  | Engine |  | Channel  |  | Validator|       |
|  +------+  +--------+  +----------+  +-----------+       |
+----------------------------------------------------------+
```

### 14.2 Plugin Interface (Python Protocol)

```python
class NotificationPlugin(Protocol):
    name: str
    async def send(self, rule: Rule, diff: Diff) -> bool:
        """Send notification."""

class URLValidatorPlugin(Protocol):
    name: str
    async def validate(self, url: str) -> bool:
        """Validate URL before monitoring."""

class AnalyticsPlugin(Protocol):
    name: str
    async def compute(self, checks: List[CheckResult]) -> Analytics:
        """Compute change analytics."""
```

### 14.3 Firecrawl Plugin

```python
class FirecrawlMonitorPlugin:
    """Use Firecrawl's monitoring API as primary backend."""
    name = "firecrawl-monitor"
    
    async def create_monitor(self, url_config: URLConfig) -> FirecrawlMonitor:
        """Create Firecrawl monitor via API."""
        response = await self.firecrawl_api.create_monitor(...)
        return self.map_to_internal(response)
    
    async def handle_webhook(self, payload: dict) -> CheckResult:
        """Process Firecrawl webhook and store results."""
        return self.transform_payload(payload)
```

---

## 15. DEPLOYMENT & DEVOPS

### 15.1 Development Environment (Docker Compose)

```yaml
# docker-compose.yml
version: '3.9'

services:
  # Backend API
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://emily:emily@db:5432/emily
      - REDIS_URL=redis://redis:6379/0
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
      - SECRET_KEY=dev-secret-key-change-in-prod
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker (self-hosted fallback only)
  worker:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://emily:emily@db:5432/emily
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A app.celery_app worker --concurrency=4 --loglevel=info

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1
    depends_on:
      - api

  # Database
  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=emily
      - POSTGRES_USER=emily
      - POSTGRES_PASSWORD=emily
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Cache / Broker
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Object Storage (local S3 alternative)
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
```

### 15.2 Production Deployment Options

**Option A: Managed Cloud (Recommended for SaaS)**
- Cloudflare (DNS + WAF + CDN)
- AWS Application Load Balancer
- ECS Fargate (or EKS)
- RDS PostgreSQL (Multi-AZ), ElastiCache Redis, S3, SES
- Estimated: $200-500/month + Firecrawl credits

**Option B: VPS (Budget)**
- DigitalOcean / Linode / Hetzner (4GB+ RAM)
- Docker Compose: FastAPI + Nginx, Celery, PostgreSQL, Redis, MinIO
- Estimated: $20-40/month + Firecrawl credits

**Option C: Kubernetes (Scale)**
- EKS / GKE / AKS
- Ingress Controller, Deployments for api-server, celery-worker, celery-beat, frontend
- RDS PostgreSQL + ElastiCache + S3
- Prometheus + Grafana (monitoring)
- Estimated: $500-2000/month + Firecrawl credits

---

## 16. IMPLEMENTATION ROADMAP

### Phase 1: MVP (Weeks 1-4)

```
Week 1: Foundation
  - Project setup (FastAPI, SQLAlchemy, Alembic)
  - Database schema + migrations
  - Auth system (register, login, JWT)
  - Basic URL CRUD API
  - Docker Compose dev environment
  - Firecrawl API integration (create/list/update/delete monitors)

Week 2: Firecrawl Webhooks
  - Webhook endpoint for Firecrawl events
  - Store check results in PostgreSQL
  - Basic diff viewer (text + JSON)
  - Firecrawl monitor management UI

Week 3: Self-Hosted Fallback
  - Celery workers for polling
  - Playwright/httpx fetching
  - readability-lxml extraction
  - difflib-based diffing
  - Switch between Firecrawl and self-hosted per URL

Week 4: Notifications
  - Email notifications (SMTP)
  - Webhook notifications
  - Notification rules per URL
  - Alert configuration UI

Deliverable: Functional MVP with Firecrawl as primary, self-hosted as fallback
```

### Phase 2: Polish & Scale (Weeks 5-8)

```
Week 5: Analytics
  - Change frequency tracking
  - Trend detection (price decreasing, etc.)
  - Anomaly detection (spike in changes)
  - Analytics dashboard

Week 6: UI Polish
  - Diff viewer improvements (unified, side-by-side, JSON, AI summary)
  - Snapshot timeline
  - Responsive design
  - Dark mode

Week 7: Advanced Features
  - Bulk URL import (CSV)
  - Export functionality
  - Tag-based filtering
  - Search across URLs

Week 8: Monitoring & Observability
  - Prometheus metrics
  - Health check endpoints
  - Structured logging
  - Error tracking (Sentry)

Deliverable: Production-ready platform with analytics
```

### Phase 3: SaaS Features (Weeks 9-12)

```
Week 9: Multi-tenancy
  - Tenant isolation
  - Plan management (free, pro, enterprise)
  - Usage quotas
  - Tenant settings

Week 10: Advanced Notifications
  - Slack integration
  - Telegram integration
  - Discord integration
  - Notification templates

Week 11: API & Integrations
  - API key system
  - OpenAPI documentation
  - Webhook delivery logs
  - Programmatic URL management

Week 12: Polish & Launch
  - Security hardening
  - Performance optimization
  - Documentation
  - Beta launch

Deliverable: Full SaaS platform ready for launch
```

### Phase 4: Growth (Months 4-6)

- Mobile app (React Native)
- Browser extension for one-click monitoring
- Team collaboration features
- Custom extraction rules (JSON config)
- Plugin marketplace
- White-label option for agencies
- Self-hosted enterprise version

---

## 17. TECHNOLOGY RECOMMENDATIONS SUMMARY

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Backend Framework** | FastAPI (Python) | Async-native, auto OpenAPI docs, excellent ecosystem |
| **Language** | Python 3.12+ | FastAPI, SQLAlchemy, Firecrawl SDK, readability-lxml |
| **ORM** | SQLAlchemy 2.0 | Async support, mature, excellent migration tooling (Alembic) |
| **Database** | PostgreSQL 16+ | JSONB for flexible config, excellent indexing, row-level security |
| **Cache/Session** | Redis 7 | Rate limiting, caching, session storage |
| **Object Storage** | S3/MinIO | Cheap storage for raw HTML snapshots, scalable |
| **Frontend Framework** | React 18 + TypeScript | Component-based, strong ecosystem, type safety |
| **Build Tool** | Vite | Fast HMR, excellent DX, modern |
| **Styling** | TailwindCSS + shadcn/ui | Rapid UI development, accessible components |
| **Diff Viewer** | diff2html | Best balance of features and simplicity |
| **Code Diff** | monaco-editor | VS Code quality, optional for code-heavy pages |
| **HTTP Client** | httpx (async) | Async, supports cookies, headers, sessions |
| **Browser Automation** | Playwright | JS rendering for self-hosted fallback |
| **Content Extraction** | readability-lxml + trafilatura | Article extraction, text cleaning |
| **Diff Engine** | difflib (std) + custom semantic | Line-level + paragraph-level diffs (self-hosted) |
| **Task Queue** | Celery + Redis | Self-hosted polling (fallback only) |
| **Auth** | JWT + refresh tokens | Stateless, scalable, standard for APIs |
| **Password Hashing** | bcrypt | Industry standard |
| **Validation** | Pydantic v2 | Fast, type-safe request/response validation |
| **Testing** | pytest + httpx + factory-boy | Comprehensive testing |
| **Monitoring** | Prometheus + Grafana | Metrics + dashboards |
| **Error Tracking** | Sentry | Exception tracking, performance monitoring |
| **Container** | Docker + Docker Compose | Dev and prod consistency |
| **CI/CD** | GitHub Actions | Automated testing, building, deployment |
| **Primary Backend** | Firecrawl Monitoring API | Scraping + AI diffing + structured extraction |
| **Fallback Backend** | Self-hosted polling | Celery + Playwright + readability-lxml + difflib |

---

## 18. PROJECT STRUCTURE

```
emily-web-delta/
+-- backend/
|   +-- app/
|   |   +-- __init__.py
|   |   +-- main.py                    # FastAPI app, middleware
|   |   +-- config.py                  # Settings (Pydantic BaseSettings)
|   |   +-- celery_app.py              # Celery configuration (self-hosted only)
|   |   +-- __pycache__/
|   |   +-- api/                       # API routes
|   |   |   +-- __init__.py
|   |   |   +-- auth.py                # Auth endpoints
|   |   |   +-- urls.py                # URL CRUD
|   |   |   +-- checks.py              # Check results endpoints
|   |   |   +-- diffs.py               # Diff endpoints
|   |   |   +-- notifications.py       # Notification rules
|   |   |   +-- admin.py               # Admin endpoints
|   |   |   +-- webhooks.py            # Firecrawl webhook endpoint
|   |   |   +-- analytics.py           # Analytics endpoints
|   |   +-- core/                      # Core business logic
|   |   |   +-- security.py            # Auth, password hashing
|   |   |   +-- rate_limit.py          # Rate limiting
|   |   |   +-- scheduler.py           # URL polling scheduler (self-hosted)
|   |   |   +-- diff_engine.py         # Diff computation (self-hosted)
|   |   |   +-- html_parser.py         # HTML extraction (self-hosted)
|   |   |   +-- url_validator.py      # URL validation
|   |   +-- models/                    # SQLAlchemy models
|   |   |   +-- user.py
|   |   |   +-- tenant.py
|   |   |   +-- url.py
|   |   |   +-- snapshot.py
|   |   |   +-- diff.py
|   |   |   +-- notification.py
|   |   |   +-- api_key.py
|   |   |   +-- audit_log.py
|   |   |   +-- firecrawl_monitor.py
|   |   |   +-- check_result.py
|   |   +-- schemas/                   # Pydantic models
|   |   |   +-- user.py
|   |   |   +-- url.py
|   |   |   +-- snapshot.py
|   |   |   +-- diff.py
|   |   |   +-- notification.py
|   |   |   +-- firecrawl.py
|   |   +-- services/                  # Business logic services
|   |   |   +-- url_service.py
|   |   |   +-- snapshot_service.py
|   |   |   +-- diff_service.py
|   |   |   +-- notification_service.py
|   |   |   +-- storage_service.py     # S3/MinIO operations
|   |   |   +-- firecrawl_service.py   # Firecrawl API integration
|   |   |   +-- analytics_service.py   # Change analytics
|   |   +-- workers/                   # Celery tasks (self-hosted only)
|   |   |   +-- polling.py             # URL polling task
|   |   |   +-- diff_processing.py     # Diff computation task
|   |   |   +-- notifications.py       # Notification dispatch
|   |   +-- plugins/                   # Plugin system
|   |   |   +-- base.py                # Plugin base classes
|   |   |   +-- notifications/         # Notification plugins
|   |   |   +-- analytics/             # Analytics plugins
|   |   +-- db/                        # Database utilities
|   |       +-- session.py
|   |       +-- alembic/               # Migrations
|   +-- tests/
|   +-- alembic.ini
|   +-- pyproject.toml
|   +-- Dockerfile
|   +-- requirements.txt
|
+-- frontend/
|   +-- src/
|   |   +-- main.tsx
|   |   +-- App.tsx
|   |   +-- components/
|   |   |   +-- layout/                # Header, sidebar, nav
|   |   |   +-- urls/                  # URL list, form, editor
|   |   |   +-- diffs/                 # Diff viewer components
|   |   |   +-- checks/                # Check results list
|   |   |   +-- notifications/         # Notification config
|   |   |   +-- analytics/             # Analytics dashboard
|   |   +-- pages/
|   |   |   +-- dashboard.tsx
|   |   |   +-- url-list.tsx
|   |   |   +-- url-detail.tsx
|   |   |   +-- checks.tsx
|   |   |   +-- diffs.tsx
|   |   |   +-- analytics.tsx
|   |   |   +-- settings.tsx
|   |   |   +-- admin.tsx
|   |   +-- hooks/                     # Custom React hooks
|   |   +-- lib/                       # API client, utils
|   |   +-- store/                     # Zustand stores
|   |   +-- types/                     # TypeScript types
|   +-- package.json
|   +-- vite.config.ts
|   +-- tsconfig.json
|   +-- Dockerfile
|   +-- nginx.conf
|
+-- docker-compose.yml
+-- docker-compose.prod.yml
+-- docs/
|   +-- architecture.md                # This document
|   +-- api.md                         # API documentation
|   +-- deployment.md                  # Deployment guide
+-- README.md
```

---

## 19. KEY DESIGN DECISIONS & RATIONALE

### 19.1 Why Firecrawl as Primary Backend?

1. **AI-powered change judging** — The `goal` field + LLM judging is genuinely novel. You pass "Alert when price changes" and the LLM judges each change, returns `meaningful`, `confidence`, `reason`. This is what we planned to build with semantic diffing, but Firecrawl has it production-ready.

2. **JSON-mode structured extraction** — Define a Pydantic/zod schema, get per-field diffs like `plans[0].price: {previous: "$19/mo", current: "$24/mo"}`. This is exactly the structured field extraction we planned but hadn't seen done this cleanly.

3. **Crawl monitors** — Auto-discovers all pages on a site and diffs them each check. Saves weeks of custom crawler development.

4. **Development speed** — Cuts ~40% of development effort (weeks 2-5 of Phase 1-2). We go from zero to functional product in 4 weeks instead of 8-10.

5. **Diff quality** — Unified text diff + JSON diff + AI summary is superior to self-built heuristic diffing.

### 19.2 Why Self-Hosted as Fallback?

1. **Cost control** — For high-frequency monitoring (5 min intervals), Firecrawl credits can be expensive. Self-hosted has zero marginal cost.

2. **Air-gapped deployments** — Some users cannot make external API calls. Self-hosted is the only option.

3. **Full control** — For users who want to customize extraction, diffing, or storage.

4. **Vendor lock-in mitigation** — Users can switch between Firecrawl and self-hosted per URL.

### 19.3 Why Not Firecrawl-Only?

1. **Cost at scale** — 100 URLs at 5-min intervals = ~$14,400 credits/month. Self-hosted is $0 marginal cost.

2. **No self-hosting option** — Firecrawl is cloud-only. Our product must support self-hosting.

3. **Differentiation** — If we're just a Firecrawl wrapper, we have no moat. The self-hosted fallback gives us a unique selling point.

### 19.4 Why Monolith?

1. **Speed to market** — Deploy one service, not 5.
2. **Debugging** — Same process, same logs, same stack traces.
3. **Team size** — 1-3 developers can manage a monolith easily.
4. **No distributed transactions** — URL CRUD + check storage + diff computation can all happen in one DB transaction.
5. **Easy decomposition** — Clear module boundaries mean services can be extracted when needed.

---

## 20. RISKS & MITIGATIONS

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Firecrawl price increases | High | Medium | Self-hosted fallback, negotiate enterprise pricing |
| Firecrawl API changes | Medium | Low | Abstract API behind service layer, version API |
| Vendor lock-in | High | Medium | Per-URL backend selection, export tools |
| Credit cost overruns | Medium | High | Usage alerts, budget caps, self-hosted fallback |
| Storage growth | Medium | High | Snapshot pruning, S3 lifecycle policies, compression |
| Security vulnerability in stored HTML | High | Medium | HTML sanitization, CSP headers, DOMPurify, no inline scripts |
| Scale beyond monolith | Medium | Low | Clear module boundaries, extract polling worker first |
| Firecrawl outage | Medium | Low | Self-hosted fallback, retry logic, caching |

---

## 21. COST ESTIMATES

### 21.1 Development Phase (Self-Hosted + Firecrawl)

| Component | Cost |
|-----------|------|
| VPS (4GB RAM, 2 vCPU) | $20-40/month |
| PostgreSQL (on VPS) | Included |
| Redis (on VPS) | Included |
| MinIO (on VPS) | Included |
| Domain + SSL | $10-15/year |
| Firecrawl credits (100 URLs, daily) | ~$288/month |
| **Total** | **$300-350/month** |

### 21.2 Production SaaS

| Component | Cost |
|-----------|------|
| AWS Application Load Balancer | $20/month |
| ECS Fargate (2-4 tasks) | $50-100/month |
| RDS PostgreSQL (db.t3.small) | $50/month |
| ElastiCache Redis (cache.t3.micro) | $15/month |
| S3 (snapshot storage) | $5-20/month |
| SES (email delivery) | $0.10/1000 emails |
| Cloudflare (DNS + WAF) | Free-$20/month |
| Sentry (error tracking) | Free-$25/month |
| Firecrawl credits (varies by usage) | $0.01-0.05/scrape |
| **Total** | **$150-250/month + Firecrawl credits** |

### 21.3 Scale Production

| Component | Cost |
|-----------|------|
| Kubernetes (EKS/GKE) | $100-200/month |
| PostgreSQL (Multi-AZ) | $200-400/month |
| ElastiCache Redis | $50-100/month |
| S3 + CloudFront | $50-100/month |
| ECS/EKS compute | $300-500/month |
| Firecrawl credits (varies by usage) | $0.01-0.05/scrape |
| **Total** | **$700-1200/month + Firecrawl credits** |

### 21.4 Cost Comparison: Firecrawl vs Self-Hosted

| Scenario | Firecrawl Credits | Self-Hosted Infra | Total |
|----------|------------------|-------------------|-------|
| 100 URLs, daily | $288 | $20 | $308/month |
| 100 URLs, hourly | $2,160 | $20 | $2,180/month |
| 100 URLs, 5-min | $14,400 | $40 | $14,440/month |
| 10 URLs, daily | $28.80 | $20 | $48.80/month |
| 10 URLs, 5-min | $1,440 | $40 | $1,480/month |

**Key insight:** For low-frequency monitoring (daily or hourly), Firecrawl credits are reasonable. For high-frequency (5-min intervals), self-hosted is significantly cheaper.

---

## END OF DOCUMENT

This architecture document presents a comprehensive blueprint for building Emily Web Delta — a web page change monitoring platform. The recommended approach is a **Python/FastAPI modular monolith** with **Firecrawl Monitoring API as the primary backend** for scraping, AI-powered diffing, and structured extraction, with a **self-hosted fallback** (Celery + Playwright + readability-lxml + difflib) for cost-sensitive or air-gapped deployments.

The key differentiator is the combination of:
1. **Firecrawl's AI judging** for meaningful change detection
2. **JSON-mode structured extraction** for per-field diffs
3. **Multi-tenant team collaboration** (which Firecrawl lacks)
4. **Self-hosting option** (which Firecrawl lacks)
5. **Change analytics** (frequency, trends, anomaly detection)
6. **Plugin system** for extensible notifications and analytics

This positions Emily Web Delta as a **complete monitoring platform** — not just a wrapper around Firecrawl, but a full-featured SaaS that combines the best of both worlds: Firecrawl's AI-powered extraction and our own UI, multi-tenancy, and analytics.
