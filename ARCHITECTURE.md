# Emily Web Delta — Architecture & Research Document

> **Author:** Lucas Fontaine (CTO/Co-Founder) via Hermes Agent
> **Date:** 2026-05-28
> **Status:** Initial Architecture Research & Planning Document
> **Project Name:** emily-web-delta

---

## TABLE OF CONTENTS

1. Executive Summary
2. Problem Statement & Use Cases
3. Competitive Landscape Analysis
4. System Architecture Overview
5. Change Detection Strategies
6. Content Extraction & Normalization
7. Diff Algorithms & Delta Computation
8. Backend Tech Stack Evaluation
9. Frontend Tech Stack Evaluation
10. Database Schema Design
11. API Design
12. Security Architecture
13. Monitoring, Alerting & Notifications
14. Performance & Scalability
15. Extensibility & Plugin System
16. Deployment & DevOps
17. Implementation Roadmap
18. Technology Recommendations Summary
19. Project Structure
20. Key Design Decisions & Rationale
21. Risks & Mitigations
22. Cost Estimates

---

## 1. EXECUTIVE SUMMARY

This document presents a comprehensive architecture for **Emily Web Delta** — a self-hosted, web-based platform for monitoring configurable URLs, detecting content changes, computing meaningful deltas, and providing a rich web UI for browsing diffs and receiving alerts.

**Key architectural decision: Modular monolith with clear boundaries.**

For early-stage development, a well-structured monolith is optimal. Module boundaries are clearly defined so that the polling engine, diff engine, API server, and web UI can be extracted independently if scale demands it.

**Recommended stack:**
- **Backend:** Python 3.12+ with FastAPI (async), SQLAlchemy (ORM), Celery (task queue)
- **Frontend:** React 18+ with TypeScript, Vite, TailwindCSS, diff2html
- **Database:** PostgreSQL 16+ (primary), Redis (cache + broker)
- **Task Queue:** Celery + Redis
- **Content Extraction:** readability-lxml + trafilatura
- **JS Rendering:** Playwright (optional, per-URL)
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
- Meaningful diff computation (not just raw HTML comparison)
- Web-based UI for full interaction
- Notification system (email, webhook, Slack, etc.)
- Snapshot history with timeline view
- Delta visualization (side-by-side, unified, semantic)

---

## 3. COMPETITIVE LANDSCAPE ANALYSIS

### 3.1 changedetection.io (31,752 stars, Python, Apache-2.0)

The dominant open-source player. Self-hosted, Docker-based, with browser-based UI.

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

**Gaps / Opportunities:**
- Diff quality is limited — primarily text-based line diffing
- No semantic/paragraph-level diffing
- No structured field extraction (price, stock, etc.)
- No multi-tenancy or team collaboration
- No API-first design (primarily a single-user tool)
- No pricing tiers or SaaS features
- No advanced analytics (change frequency, uptime, trend analysis)
- Single-tenant by design — no user accounts, no organizations

### 3.2 ArchiveBox (27,562 stars, Python, MIT)

Web archiving tool — saves complete page snapshots (HTML, JS, PDF, media, screenshots).

**Strengths:**
- Comprehensive archiving (HTML, PDF, screenshots, media)
- Supports bookmarks, Pinboard, Pocket, browser history import
- Docker-based, self-hosted
- Rich export options (WARC, singlefile)

**Gaps / Opportunities:**
- Not designed for change detection — it's an archiving tool
- No diff computation between snapshots
- No alerting/notification system
- No structured change tracking
- Overkill for monitoring use case (stores everything)

### 3.3 Visualping (Commercial SaaS)

The leading commercial web monitoring service.

**Strengths:**
- Excellent visual diff (screenshot-based comparison)
- Smart change detection (ignores ads, navigation, timestamps)
- Email/webhook notifications
- API access
- Trusted brand, enterprise customers

**Gaps / Opportunities:**
- Paid service (not free/open-source)
- Limited free tier
- No self-hosted option
- Limited customization
- No semantic diffing or structured data extraction
- No team collaboration features in lower tiers

### 3.4 Wachete (Commercial SaaS)

Another commercial web monitoring service with similar feature set.

**Strengths:**
- Good diff quality
- Multiple notification channels
- Clean UI
- API access

**Gaps / Opportunities:**
- Paid service
- Limited open-source alternatives
- No self-hosted option

### 3.5 Distill.io (Commercial SaaS)

Enterprise-focused web monitoring with advanced features.

**Strengths:**
- Enterprise-grade features
- Advanced filtering
- API access
- Team collaboration

**Gaps / Opportunities:**
- Expensive (enterprise pricing)
- No self-hosted option
- Complex setup

### 3.6 Market Gap Analysis

| Feature | changedetection.io | Visualping | Distill | Emily Web Delta |
|---------|-------------------|------------|---------|-----------------|
| Self-hosted | Yes | No | No | Yes |
| Open-source | Yes | No | No | Yes |
| Free tier | Yes (full) | Limited | No | Yes |
| Semantic diff | No | Partial | Partial | Yes |
| Structured extraction | No | No | No | Yes |
| Multi-tenancy | No | Yes | Yes | Yes |
| Team collaboration | No | Yes | Yes | Yes |
| API-first | Partial | Yes | Yes | Yes |
| Plugin system | No | No | No | Yes |
| Change analytics | No | No | Limited | Yes |
| Browser extension | No | Yes | No | Future |
| Mobile app | No | No | No | Future |

**Key Differentiators for Emily Web Delta:**
1. **Semantic diffing** — paragraph-level, field-level, not just line-level
2. **Structured data extraction** — recognize prices, dates, stock levels, etc.
3. **Multi-tenant SaaS** — team collaboration, organizations, plans
4. **Plugin system** — extensible parsers, diff engines, notification channels
5. **Change analytics** — frequency analysis, trend detection, anomaly alerts
6. **API-first design** — full programmatic access from day one

---

## 4. SYSTEM ARCHITECTURE OVERVIEW

### 4.1 High-Level Component Diagram

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
|                           |         WORKER LAYER                   |
|  +------------------------+----------------------------------------+|
|  |     Celery Workers                                      |        ||
|  |  +------------------+ +-------------------------------+  |  ||
|  |  |  Polling Worker  | |  Diff/Processing Worker       |  |  ||
|  |  |  (fetch + hash)  | |  (content extraction + diff)  |  |  ||
|  |  +------------------+ +-------------------------------+  |  ||
|  +-----------------------------------------------------------+||
|                           |                                        |
+---------------------------+----------------------------------------+
|                           |         DATA LAYER                     |
|  +------------------------+----------------------------------------+|
|  |  PostgreSQL  ------  |  ------  Redis                          ||
|  |  (URLs, Snapshots,  |  (Rate limit counters,                   ||
|  |   Users, Configs)   |   Celery broker,                         ||
|  +----------------------+   Cache, Job queue)                    ||
|  +------------------------+----------------------------------------+|
|  |  Object Storage (S3/  |  ------  Log Aggregation               ||
|  |  MinIO)               |  ------  (Prometheus + Grafana)        ||
|  +------------------------+----------------------------------------+|
+------------------------------------------------------------------+
```

### 4.2 Data Flow

```
1. POLLING CYCLE:
   Scheduler (Celery Beat)
        |
        v
   [Check intervals] -> Identify URLs due for polling
        |
        v
   Celery Queue: "url_poll" task
        |
        v
   Polling Worker:
     a. HTTP GET (with configurable headers, cookies, JS rendering)
     b. Content normalization (strip ads, nav, whitespace)
     c. SHA-256 hash computation
     d. Hash comparison with last_hash
        |
        v
   IF hash differs:
     - Publish to "url_diff" queue
     - Update last_hash, last_checked in DB
   ELSE:
     - Skip (no change)

2. DIFF PROCESSING:
   Celery Queue: "url_diff" task
        |
        v
   Diff Worker:
     a. Fetch previous snapshot from DB
     b. Run diff algorithm (line-level + semantic)
     c. Store new snapshot
     d. Store diff result
        |
        v
   Notification Service:
     a. Evaluate notification rules
     b. Send email/webhook/Slack
     c. Update notification log

3. USER QUERY:
   Web UI -> API GET /api/v1/urls/{id}/diffs/{from}/{to}
        |
        v
   API Server -> Query DB for snapshots
        |
        v
   Return diff JSON or rendered HTML diff
```

### 4.3 Monolith vs Microservices Decision Matrix

| Criterion | Monolith (Recommended) | Microservices |
|-----------|----------------------|---------------|
| Team size (1-3) | Excellent | Overkill |
| Dev speed | Fastest | Slower (network, deployment) |
| Debugging | Simple (same process) | Complex (distributed tracing) |
| Deployment | Single deploy | Multiple services |
| Scaling | Scale as unit | Scale per service |
| Data consistency | ACID via DB | Eventual consistency |
| Operational cost | Low | High |
| Failure isolation | None (process-wide) | Good (service isolation) |
| Future decomposition | Clear module boundaries | N/A |

**Recommendation:** Start with modular monolith. Extract the Polling Worker as a separate service when you hit >1000 URLs or need independent scaling.

---

## 5. CHANGE DETECTION STRATEGIES

### 5.1 Strategy Comparison

| Strategy | How It Works | Pros | Cons | Best For |
|----------|-------------|------|------|----------|
| **Hash-based polling** | Compute SHA-256 of content, compare with last hash | Simple, reliable, efficient | Misses changes if hash function is too strong | General purpose |
| **DOM-based diffing** | Parse HTML into DOM tree, compare nodes | Captures structural changes | Complex, slow | Structured pages |
| **Visual diffing** | Take screenshots, compare pixel-by-pixel | Shows exactly what changed | Heavy storage, slow | Visual changes |
| **XPath/CSS filtering** | Extract specific elements, compare | Precise, ignores noise | Requires per-URL config | Targeted monitoring |
| **MutationObserver** | Browser extension watches for DOM changes | Real-time, no polling | Requires browser extension | Personal use |
| **RSS/Atom feed** | Monitor feed for new entries | Simple, standardized | Only works for sites with feeds | Blogs, news |
| **API polling** | Poll REST/GraphQL APIs | Structured data, reliable | Only works for API endpoints | API monitoring |

### 5.2 Recommended Approach: Multi-Layer Detection

The recommended approach combines multiple strategies:

1. **Primary: Hash-based polling** (fast change detection)
   - Compute SHA-256 of extracted text content
   - If hash differs, trigger full diff pipeline
   - Configurable interval per URL (5 min to 24 hours)

2. **Secondary: Content extraction** (meaningful diffing)
   - Use readability-lxml to extract main content
   - Strip navigation, ads, footers, timestamps
   - Normalize whitespace and dynamic elements

3. **Tertiary: Targeted extraction** (precision)
   - XPath/CSS selectors for specific elements
   - JSON path extraction for API responses
   - Configurable per URL

4. **Optional: JS-rendered pages** (dynamic content)
   - Playwright for JavaScript-heavy pages
   - Configurable per URL (enabled/disabled)
   - Wait for specific elements to load

### 5.3 Polling Interval Strategy

```
Interval tiers:
- Critical (1 min):    Price pages, stock availability, incident reports
- High (5 min):        Job listings, news updates, regulatory pages
- Medium (30 min):     Blog posts, product pages, pricing pages
- Low (2 hours):       Terms of service, policy pages, documentation
- Custom (N min):      User-defined interval

Smart scheduling:
- Adaptive intervals: Increase interval after periods of no change
- Burst protection: Limit concurrent polls to prevent IP bans
- Rate limiting: Per-URL rate limits based on target site policies
- Respect robots.txt: Optional compliance with site policies
```

---

## 6. CONTENT EXTRACTION & NORMALIZATION

### 6.1 Extraction Pipeline

```
Raw HTML
    |
    v
[1] HTTP Fetch (with headers, cookies, JS rendering if needed)
    |
    v
[2] HTML Cleaning (html5lib parser, remove scripts/styles)
    |
    v
[3] Content Extraction (readability-lxml OR trafilatura)
    |
    v
[4] Targeted Extraction (XPath/CSS selectors, JSON path)
    |
    v
[5] Normalization (whitespace, dynamic elements, sorting)
    |
    v
[6] Hash Computation (SHA-256 of normalized text)
    |
    v
[7] Store (raw HTML + extracted text + metadata)
```

### 6.2 Extraction Libraries Comparison

| Library | Language | Strengths | Weaknesses | Best For |
|---------|----------|-----------|------------|----------|
| **readability-lxml** | Python | Mozilla's Readability algorithm, excellent article extraction | May miss non-article content | Blog posts, articles, news |
| **trafilatura** | Python | Multi-language support, markdown output, metadata extraction | Less refined for some page types | Multilingual sites, structured content |
| **BeautifulSoup** | Python | Flexible, handles malformed HTML, easy to use | No built-in content extraction | Custom extraction rules |
| **lxml** | Python | Fast, XPath support, HTML5 parsing | Lower-level API, more code | Performance-critical extraction |
| **cheerio** | Node.js | jQuery-like API, fast | No semantic extraction | Node.js-based pipelines |
| **Playwright** | Python/Node | Full browser, JS rendering, screenshots | Slow, heavy resource usage | Dynamic/JS-heavy pages |

### 6.3 Recommended Extraction Strategy

**Default pipeline:** readability-lxml (for article-style content) + BeautifulSoup fallback (for other pages)

**Per-URL override:** Users can specify:
- Extraction method (readability, trafilatura, custom)
- XPath/CSS selectors for targeted extraction
- JSON path for API responses
- Custom normalization rules

### 6.4 Normalization Rules

```python
# Dynamic element removal
- Timestamps/dates (regex-based)
- Random IDs/classes
- Session tokens in URLs
- Ad tracking parameters

# Whitespace normalization
- Collapse multiple whitespace to single space
- Normalize line endings
- Strip leading/trailing whitespace

# Sorting normalization
- Sort list items if order is irrelevant
- Sort JSON keys for consistent hashing
- Normalize date formats to canonical form

# Content filtering
- Remove elements matching CSS selectors
- Remove elements with specific text patterns
- Keep only specified elements (whitelist mode)
```

---

## 7. DIFF ALGORITHMS & DELTA COMPUTATION

### 7.1 Diff Algorithm Comparison

| Algorithm | Granularity | Speed | Quality | Library | Best For |
|-----------|------------|-------|---------|---------|----------|
| **Line-level** | Line | Fast | Moderate | difflib (Python), diff (Node.js) | Text content, code |
| **Word-level** | Word | Medium | Good | python-Levenshtein, diff-match-patch | Fine-grained changes |
| **Paragraph-level** | Paragraph | Medium | Good | Custom (split by \n\n) | Article content |
| **DOM-level** | Node | Slow | Excellent | Custom (tree diff) | HTML structure |
| **Semantic** | Field/Concept | Slow | Best | Custom (pattern matching) | Prices, dates, structured data |
| **Visual** | Pixel | Very Slow | Excellent | Custom (image diff) | Layout changes |

### 7.2 Recommended Diff Pipeline

```
Extracted Text
    |
    v
[1] Paragraph-level diff (split by \n\n, use SequenceMatcher)
    |
    v
[2] Word-level diff within changed paragraphs (Levenshtein)
    |
    v
[3] Semantic extraction (regex for prices, dates, numbers)
    |
    v
[4] Structured diff output (JSON with changes array)
    |
    v
[5] Render for UI (HTML diff with colors, unified/side-by-side views)
```

### 7.3 Diff Output Format

```json
{
  "diff_id": "diff-001",
  "url_id": "url-001",
  "snapshot_from": "snap-001",
  "snapshot_to": "snap-002",
  "timestamp": "2026-05-28T12:05:00Z",
  "summary": "Price changed from $19.99 to $14.99; Stock: In Stock -> Out of Stock",
  "change_count": 3,
  "lines_added": 5,
  "lines_removed": 3,
  "changes": [
    {
      "type": "value_changed",
      "field": "price",
      "old": "$19.99",
      "new": "$14.99",
      "context": "Product price on Amazon",
      "line_from": 15,
      "line_to": 15,
      "unified_diff": "- Price: $19.99\n+ Price: $14.99"
    },
    {
      "type": "value_changed",
      "field": "stock",
      "old": "In Stock",
      "new": "Out of Stock",
      "context": "Availability status",
      "line_from": 16,
      "line_to": 16,
      "unified_diff": "- Stock: In Stock\n+ Stock: Out of Stock"
    }
  ],
  "unified_diff": "@@ -14,7 +14,7 @@\n- Product: Widget Pro\n- Price: $19.99\n- Stock: In Stock\n+ Product: Widget Pro\n+ Price: $14.99\n+ Stock: Out of Stock",
  "significance": "high"
}
```

### 7.4 Diff Display Libraries

| Library | Language | Stars | Features | Best For |
|---------|----------|-------|----------|----------|
| **diff2html** | JS/TS | ~3K+ | Unified/side-by-side, syntax highlighting, RTL | React/JS frontend |
| **monaco-editor** | JS/TS | ~40K+ | VS Code editor, diff mode, syntax highlighting | Code-heavy diffs |
| **react-diff-viewer-v2** | React | ~1K+ | Simple API, word/line diffs, clean UI | Quick implementation |
| **jsdiff** | JS/TS | ~9K+ | Text differencing implementation | Backend diff computation |
| **diff-match-patch** | Multiple | ~8K+ | Google's library, high performance | Cross-language diffing |
| **go-diff** | Go | ~2K+ | Text diff/match/patch in Go | Go-based backends |

**Recommendation:** diff2html for the frontend (rich features, good React integration), jsdiff for backend computation (Python has difflib, but jsdiff is available via PyJS or we use Python's difflib).

---

## 8. BACKEND TECH STACK EVALUATION

### 8.1 Python (FastAPI) — RECOMMENDED

**Pros:**
- **HTML parsing ecosystem:** BeautifulSoup, lxml, readability-lxml, trafilatura — unmatched in Python
- **Content extraction:** readability-lxml for article extraction, trafilatura for text extraction
- **Async support:** FastAPI is async-native (Starlette + uvicorn)
- **Task queue:** Celery is the most mature Python task queue with Redis/RabbitMQ backends
- **Database ORM:** SQLAlchemy 2.0 has excellent async support
- **Diff libraries:** difflib (stdlib), python-Levenshtein, textblob for semantic comparison
- **Auto-generated OpenAPI docs:** Perfect for API-first SaaS
- **Community:** Huge community, many existing integrations

**Cons:**
- GIL limits CPU-bound parallelism (mitigated by async I/O and multiprocessing in Celery)
- Slower raw performance vs Go/Node for pure HTTP serving (but this is I/O-bound, not CPU-bound)

### 8.2 Node.js (Express/NestJS)

**Pros:**
- **Async model:** Native async/await, event loop handles thousands of concurrent connections
- **HTML parsing:** cheerio (jQuery-like), jsdom (full browser DOM)
- **Unified language:** JavaScript/TypeScript across frontend and backend
- **Real-time:** Native WebSocket support via ws or socket.io

**Cons:**
- **HTML parsing quality:** cheerio lacks semantic extraction quality of Python's readability-lxml
- **Content extraction:** No equivalent to readability-lxml or trafilatura
- **Diff libraries:** diff npm package is basic, no semantic diffing out of the box

### 8.3 Go

**Pros:**
- **Performance:** Excellent for concurrent HTTP polling (goroutines are lightweight)
- **Deployment:** Single binary, no runtime dependencies
- **Memory:** Very low memory footprint per worker

**Cons:**
- **HTML parsing:** goquery exists but ecosystem is thin compared to Python
- **Content extraction:** Would need to implement or port extraction logic
- **Development speed:** Slower iteration than Python for prototyping

### 8.4 Final Recommendation

**Go with Python (FastAPI) as the primary backend.**

Justification:
1. **Content extraction is the core differentiator.** Python's readability-lxml, trafilatura, and BeautifulSoup provide production-quality HTML cleaning and article extraction.
2. **FastAPI's async model** handles the I/O-bound polling workload well.
3. **Celery + Redis** provides a battle-tested task queue.
4. **FastAPI auto-generates OpenAPI docs** — critical for a SaaS product.

---

## 9. FRONTEND TECH STACK EVALUATION

### 9.1 Recommended Stack

**React 18+ + TypeScript + Vite + diff2html + TailwindCSS**

Justification:
1. **diff2html** provides the best balance of features and ease of use:
   - Unified and side-by-side views
   - Syntax highlighting
   - RTL support
   - Rich customization options

2. **monaco-editor** as an alternative view mode for code-heavy pages:
   - Toggle between "visual diff" and "code diff"
   - Monaco's diff editor is the gold standard for code comparison

3. **TailwindCSS** for rapid, consistent styling

4. **Zustand** for state management (lightweight) or **TanStack Query** for server state caching

5. **React Router v6** for routing

### 9.2 Diff Display UI Components

```
+----------------------------------------------------------+
|  URL: example.com/product-page                           |
|  Last checked: 2 min ago  |  Interval: 5 min  |  [Refresh]|
+----------------------------------------------------------+
|  [Unified] [Side-by-Side] [Semantic] [Code]              |
+----------------------------------------------------------+
|  +----------------------------------------------------+  |
|  |  <del>- Price: $19.99                            </del>|
|  |  <ins>+ Price: $14.99                            </ins>|
|  |  <del>- Stock: In Stock                          </del>|
|  |  <ins>+ Stock: Out of Stock                      </ins>|
|  +----------------------------------------------------+  |
+----------------------------------------------------------+
|  +----------------------------------------------------+  |
|  |  Semantic Diff                                     |  |
|  |  Price changed: $19.99 -> $14.99 (-25%)            |  |
|  |  Stock status changed: In Stock -> Out of Stock    |  |
|  +----------------------------------------------------+  |
+----------------------------------------------------------+
|  [Snapshot Timeline]                                     |
|  O---O---O---O---O---O---O---O---O---O                    |
|  Jan Feb Mar Apr May Jun Jul Aug Sep Oct                 |
+----------------------------------------------------------+
```

---

## 10. DATABASE SCHEMA DESIGN

### 10.1 Entity Relationship Diagram

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
| url          |       | content          |  <- large text/blob
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
+--------------+       +------------------+
                       +------------------+
                       | id (PK)          |
                       | snapshot_from(FK)|
                       | snapshot_to (FK) |
                       | diff_type        |  <- unified|semantic
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

### 10.2 Detailed Table Definitions

```sql
-- Users table (for multi-user SaaS)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenants/Organizations (for multi-tenant SaaS)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    max_urls INT DEFAULT 10,
    max_snapshots_per_url INT DEFAULT 30,
    max_diffs_per_url INT DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- URLs to monitor
CREATE TABLE urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(2048) NOT NULL,
    normalized_url VARCHAR(2048) NOT NULL,
    interval_seconds INT DEFAULT 300,
    enabled BOOLEAN DEFAULT TRUE,
    last_checked TIMESTAMPTZ,
    last_hash VARCHAR(64),
    next_check TIMESTAMPTZ,
    headers JSONB DEFAULT '{}',
    cookies JSONB DEFAULT '{}',
    js_required BOOLEAN DEFAULT FALSE,
    max_retries INT DEFAULT 3,
    user_agent VARCHAR(255),
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, normalized_url)
);

-- Content snapshots
CREATE TABLE url_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_id UUID REFERENCES urls(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL,
    content TEXT,
    extracted_text TEXT,
    content_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    snapshot_size INT,
    content_length INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_snapshots_url_created (url_id, created_at DESC)
);

-- Diff records (link two snapshots)
CREATE TABLE url_diffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_id UUID REFERENCES urls(id) ON DELETE CASCADE,
    snapshot_from UUID REFERENCES url_snapshots(id),
    snapshot_to UUID REFERENCES url_snapshots(id),
    diff_type VARCHAR(20) DEFAULT 'unified',
    diff_content JSONB NOT NULL,
    diff_size INT,
    is_significant BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_diffs_url_created (url_id, created_at DESC)
);

-- Notification rules per URL
CREATE TABLE notification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_id UUID REFERENCES urls(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    channel VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    min_diff_size INT,
    cooldown_seconds INT DEFAULT 300,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL,
    prefix VARCHAR(10) NOT NULL,
    name VARCHAR(100),
    permissions TEXT[] DEFAULT '{"read"}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Audit log
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_urls_tenant_enabled ON urls(tenant_id, enabled);
CREATE INDEX idx_urls_next_check ON urls(next_check) WHERE enabled = TRUE;
CREATE INDEX idx_snapshots_hash ON url_snapshots(content_hash);
CREATE INDEX idx_notification_rules_tenant ON notification_rules(tenant_id, enabled);
```

### 10.3 Storage Strategy for Snapshots

```
Decision: Store raw HTML in object storage (S3/MinIO), not in PostgreSQL.

Rationale:
- HTML content can be large (100KB-5MB per snapshot)
- PostgreSQL TEXT fields are fine for moderate sizes, but object storage
  scales better and is cheaper for large blobs
- Keep extracted_text (cleaned) in PostgreSQL for diff queries
- Keep diff_content (JSON) in PostgreSQL — it's small and queried frequently

Storage hierarchy:
+-- url_snapshots.content -> S3/MinIO (raw HTML, compressed)
+-- url_snapshots.extracted_text -> PostgreSQL TEXT (cleaned, diff-ready)
+-- url_diffs.diff_content -> PostgreSQL JSONB (structured diff)
+-- url_snapshots.content_hash -> PostgreSQL VARCHAR(64) (index)
```

---

## 11. API DESIGN

### 11.1 RESTful API Endpoints

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

=== SNAPSHOTS ===
GET    /urls/:id/snapshots         # List snapshots (paginated)
GET    /urls/:id/snapshots/:snap_id  # Get snapshot details
GET    /urls/:id/snapshots/:snap_id/raw  # Get raw HTML (from S3)
GET    /urls/:id/snapshots/:snap_id/text  # Get extracted text
DELETE /urls/:id/snapshots         # Prune old snapshots

=== DIFFS ===
GET    /urls/:id/diffs             # List diffs
GET    /urls/:id/diffs/:id         # Get specific diff
GET    /urls/:id/diffs/:id/rendered  # Get rendered HTML diff
GET    /urls/:id/diffs/:id/download  # Download diff as HTML/JSON
POST   /urls/:id/diffs/compute     # Force recompute diff

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
GET    /admin/worker-status        # Celery worker health
GET    /admin/config               # System configuration
PUT    /admin/config               # Update system configuration
GET    /admin/audit-log            # Audit log (admin)

=== EXPORT ===
GET    /urls/:id/export            # Export all snapshots/diffs
GET    /urls/export                # Bulk export (all URLs)
```

---

## 12. SECURITY ARCHITECTURE

### 12.1 Threat Model

| Threat | Mitigation |
|--------|-----------|
| XSS via stored HTML | Sanitize all HTML before rendering, use CSP headers, use DOMPurify on frontend |
| Data exfiltration | Tenant isolation at DB level (tenant_id FK), Row-level security policies, API key scoping |
| DDoS / abuse | Rate limiting (Redis-based sliding window), Cloudflare/WAF in front, Request size limits |
| SQL injection | Parameterized queries (SQLAlchemy ORM), Input validation (Pydantic models), WAF rules |
| Credential theft | bcrypt/argon2 password hashing, JWT RS256, API key rotation, Audit logging |
| Unauthorized access | RBAC (tenant admin, member, read-only), Tenant ID on every query, CORS restrictions |
| Content injection | Validate URL scheme (http/https only), Block internal IPs (127.0.0.1, 10.x.x.x), URL allowlist for enterprise |

---

## 13. MONITORING, ALERTING & NOTIFICATIONS

### 13.1 Notification Channels

| Channel | Implementation | Details |
|---------|---------------|---------|
| Email | SMTP (SendGrid, AWS SES, Mailgun) | HTML + plain text diffs, configurable from/to, templates |
| Webhook | HTTP POST to arbitrary URL | JSON payload with diff summary, Retry with exponential backoff |
| Slack | Slack API (Incoming Webhook / Bot) | Rich message with diff preview, Thread per URL |
| Telegram | Telegram Bot API | Markdown-formatted diffs, Per-chat configuration |
| Discord | Discord Webhook | Embed format with diff preview |
| Push (Future) | Firebase Cloud Messaging | Mobile push notifications |

### 13.2 Notification Rules

```json
{
  "notification_rules": {
    "min_diff_size": 5,
    "cooldown_seconds": 300,
    "max_notifications_per_day": 50,
    "significant_only": true,
    "diff_thresholds": {
      "warning": 100,
      "critical": 500
    }
  }
}
```

---

## 14. PERFORMANCE & SCALABILITY

### 14.1 Concurrent Polling Architecture

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
```

### 14.2 Scaling Strategy

| Phase | URLs | Architecture | Cost |
|-------|------|-------------|------|
| Phase 1 | 0-100 | Single FastAPI + 1 Celery worker + PostgreSQL on same host | ~$10/month (VPS) |
| Phase 2 | 100-1000 | 2 FastAPI instances behind LB, 4-8 Celery workers, Managed PostgreSQL | ~$50-100/month |
| Phase 3 | 1000-10000 | Kubernetes cluster, PostgreSQL read replicas, S3 for snapshots | ~$500-1000/month |
| Phase 4 | 10000+ | Microservices decomposition, Multi-region deployment | ~$2000+/month |

### 14.3 Storage Growth Management

```
Pruning Strategy:
+----------------------------------------------------------+
| Per URL:                                                  |
|   - Keep last N snapshots (configurable, default: 30)     |
|   - Keep last M diffs (configurable, default: 10)         |
|   - Archive old snapshots to cold storage (S3 Glacier)    |
|                                                           |
| Tenant-level:                                             |
|   - Free plan: 30 snapshots, 10 diffs per URL             |
|   - Pro plan: 100 snapshots, 50 diffs per URL             |
|   - Enterprise: unlimited (with storage quota)            |
|                                                           |
| Storage Estimation:                                       |
|   Average snapshot: 100KB (compressed)                    |
|   100 URLs x 30 snapshots x 100KB = 300MB                 |
|   1000 URLs x 30 snapshots x 100KB = 3GB                  |
|   10000 URLs x 30 snapshots x 100KB = 30GB                |
+----------------------------------------------------------+
```

---

## 15. EXTENSIBILITY & PLUGIN SYSTEM

### 15.1 Plugin Architecture

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

### 15.2 Plugin Interface (Python Protocol)

```python
class HTMLParserPlugin(Protocol):
    name: str
    priority: int = 100
    async def parse(self, html: str) -> str:
        """Extract meaningful text from HTML."""

class DiffEnginePlugin(Protocol):
    name: str
    async def compute(self, text_a: str, text_b: str) -> Diff:
        """Compute diff between two texts."""

class NotificationPlugin(Protocol):
    name: str
    async def send(self, rule: Rule, diff: Diff) -> bool:
        """Send notification."""

class URLValidatorPlugin(Protocol):
    name: str
    async def validate(self, url: str) -> bool:
        """Validate URL before monitoring."""
```

---

## 16. DEPLOYMENT & DEVOPS

### 16.1 Development Environment (Docker Compose)

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
      - SECRET_KEY=dev-secret-key-change-in-prod
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker
  worker:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://emily:emily@db:5432/emily
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A app.celery_app worker --concurrency=4 --loglevel=info

  # Celery Beat (Scheduler)
  beat:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://emily:emily@db:5432/emily
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A app.celery_app beat --loglevel=info

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

### 16.2 Production Deployment Options

**Option A: Managed Cloud (Recommended for SaaS)**
- Cloudflare (DNS + WAF + CDN)
- AWS Application Load Balancer
- ECS Fargate (or EKS)
- RDS PostgreSQL (Multi-AZ), ElastiCache Redis, S3, SES
- Estimated: $200-500/month

**Option B: VPS (Budget)**
- DigitalOcean / Linode / Hetzner (4GB+ RAM)
- Docker Compose: FastAPI + Nginx, Celery, PostgreSQL, Redis, MinIO
- Estimated: $20-40/month

**Option C: Kubernetes (Scale)**
- EKS / GKE / AKS
- Ingress Controller, Deployments for api-server, celery-worker, celery-beat, frontend
- RDS PostgreSQL + ElastiCache + S3
- Prometheus + Grafana (monitoring)
- Estimated: $500-2000/month

---

## 17. IMPLEMENTATION ROADMAP

### Phase 1: MVP (Weeks 1-4)

```
Week 1: Foundation
  - Project setup (FastAPI, SQLAlchemy, Alembic)
  - Database schema + migrations
  - Auth system (register, login, JWT)
  - Basic URL CRUD API
  - Docker Compose dev environment

Week 2: Core Monitoring
  - Polling worker (Celery task)
  - HTTP fetching with configurable headers
  - SHA-256 hash comparison
  - Snapshot storage (PostgreSQL TEXT)
  - Basic diff (line-level with difflib)

Week 3: Frontend
  - React + TypeScript + Vite setup
  - URL list page (CRUD)
  - Snapshot viewer
  - Diff viewer (diff2html)
  - Basic auth flow

Week 4: Notifications
  - Email notifications (SMTP)
  - Webhook notifications
  - Notification rules per URL
  - Alert configuration UI

Deliverable: Functional MVP with core features
```

### Phase 2: Polish & Scale (Weeks 5-8)

```
Week 5: Content Quality
  - HTML extraction (readability-lxml)
  - Semantic diff engine
  - Content normalization
  - Diff quality improvements

Week 6: Storage & Performance
  - S3/MinIO integration for raw HTML
  - Snapshot pruning
  - Redis caching layer
  - Rate limiting

Week 7: Advanced Features
  - JS-rendered page support (Playwright integration)
  - Tag-based filtering
  - Export functionality
  - Bulk URL import (CSV)

Week 8: Monitoring & Observability
  - Prometheus metrics
  - Health check endpoints
  - Structured logging
  - Error tracking (Sentry)

Deliverable: Production-ready platform with quality diffs
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
- Advanced analytics (change frequency, uptime)
- Custom extraction rules (JSON config)
- Plugin marketplace
- White-label option for agencies
- Self-hosted enterprise version

---

## 18. TECHNOLOGY RECOMMENDATIONS SUMMARY

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Backend Framework** | FastAPI (Python) | Async-native, auto OpenAPI docs, excellent HTML parsing ecosystem |
| **Language** | Python 3.12+ | BeautifulSoup, readability-lxml, trafilatura — unmatched for HTML content extraction |
| **ORM** | SQLAlchemy 2.0 | Async support, mature, excellent migration tooling (Alembic) |
| **Task Queue** | Celery + Redis | Battle-tested, excellent for distributed polling, Redis broker is lightweight |
| **Scheduler** | APScheduler | Built-in Celery beat, simple cron-like scheduling |
| **Database** | PostgreSQL 16+ | JSONB for flexible config, excellent indexing, row-level security |
| **Cache/Broker** | Redis 7 | Rate limiting, caching, Celery broker, session storage |
| **Object Storage** | S3/MinIO | Cheap storage for raw HTML snapshots, scalable |
| **Frontend Framework** | React 18 + TypeScript | Component-based, strong ecosystem, type safety |
| **Build Tool** | Vite | Fast HMR, excellent DX, modern |
| **Styling** | TailwindCSS + shadcn/ui | Rapid UI development, accessible components |
| **Diff Viewer** | diff2html | Best balance of features and simplicity, unified/side-by-side views |
| **Code Diff** | monaco-editor | VS Code quality, optional for code-heavy pages |
| **HTTP Client** | httpx (async) | Async, supports cookies, headers, sessions |
| **HTML Parsing** | readability-lxml + trafilatura | Article extraction, text cleaning |
| **Diff Engine** | difflib (std) + custom semantic | Line-level + paragraph-level diffs |
| **Auth** | JWT + refresh tokens | Stateless, scalable, standard for APIs |
| **Password Hashing** | bcrypt | Industry standard |
| **Validation** | Pydantic v2 | Fast, type-safe request/response validation |
| **Testing** | pytest + httpx + factory-boy | Comprehensive testing |
| **Monitoring** | Prometheus + Grafana | Metrics + dashboards |
| **Error Tracking** | Sentry | Exception tracking, performance monitoring |
| **Container** | Docker + Docker Compose | Dev and prod consistency |
| **CI/CD** | GitHub Actions | Automated testing, building, deployment |

---

## 19. PROJECT STRUCTURE

```
emily-web-delta/
+-- backend/
|   +-- app/
|   |   +-- __init__.py
|   |   +-- main.py                    # FastAPI app, middleware
|   |   +-- config.py                  # Settings (Pydantic BaseSettings)
|   |   +-- celery_app.py              # Celery configuration
|   |   +-- __pycache__/
|   |   +-- api/                       # API routes
|   |   |   +-- __init__.py
|   |   |   +-- auth.py                # Auth endpoints
|   |   |   +-- urls.py                # URL CRUD
|   |   |   +-- snapshots.py           # Snapshot endpoints
|   |   |   +-- diffs.py               # Diff endpoints
|   |   |   +-- notifications.py       # Notification rules
|   |   |   +-- admin.py               # Admin endpoints
|   |   |   +-- webhooks.py            # Webhook endpoints
|   |   +-- core/                      # Core business logic
|   |   |   +-- security.py            # Auth, password hashing
|   |   |   +-- rate_limit.py          # Rate limiting
|   |   |   +-- scheduler.py           # URL polling scheduler
|   |   |   +-- diff_engine.py         # Diff computation
|   |   |   +-- html_parser.py         # HTML extraction
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
|   |   +-- schemas/                   # Pydantic models
|   |   |   +-- user.py
|   |   |   +-- url.py
|   |   |   +-- snapshot.py
|   |   |   +-- diff.py
|   |   |   +-- notification.py
|   |   +-- services/                  # Business logic services
|   |   |   +-- url_service.py
|   |   |   +-- snapshot_service.py
|   |   |   +-- diff_service.py
|   |   |   +-- notification_service.py
|   |   |   +-- storage_service.py     # S3/MinIO operations
|   |   +-- workers/                   # Celery tasks
|   |   |   +-- polling.py             # URL polling task
|   |   |   +-- diff_processing.py     # Diff computation task
|   |   |   +-- notifications.py       # Notification dispatch
|   |   +-- plugins/                   # Plugin system
|   |   |   +-- base.py                # Plugin base classes
|   |   |   +-- html_parsers/          # HTML parser plugins
|   |   |   +-- diff_engines/          # Diff engine plugins
|   |   |   +-- notifications/         # Notification plugins
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
|   |   |   +-- snapshots/             # Snapshot timeline
|   |   |   +-- notifications/         # Notification config
|   |   +-- pages/
|   |   |   +-- dashboard.tsx
|   |   |   +-- url-list.tsx
|   |   |   +-- url-detail.tsx
|   |   |   +-- snapshots.tsx
|   |   |   +-- diffs.tsx
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

## 20. KEY DESIGN DECISIONS & RATIONALE

### 20.1 Why Python over Node.js/Go?

The core differentiator of this product is **meaningful diffing** — showing users *what changed* in a way that matters. Python's HTML parsing ecosystem (BeautifulSoup, readability-lxml, trafilatura) is 2-3 years ahead of Node.js equivalents in terms of quality, maturity, and ease of use. The content extraction pipeline is the heart of the product, and Python wins decisively here.

### 20.2 Why not just store HTML and diff raw?

Raw HTML diffs are noisy and unactionable. A product page might change:
- 500 lines of HTML
- But only 2 lines of actual content (price, stock)

The extraction + semantic diff pipeline is what makes this product useful. Without it, users would see "500 lines changed" and not know what actually matters.

### 20.3 Why monolith first?

1. **Speed to market:** Deploy one service, not 5.
2. **Debugging:** Same process, same logs, same stack traces.
3. **Team size:** 1-3 developers can manage a monolith easily.
4. **No distributed transactions:** URL CRUD + snapshot creation + diff computation can all happen in one DB transaction.
5. **Easy decomposition:** Clear module boundaries mean services can be extracted when needed.

### 20.4 Why PostgreSQL over MongoDB?

1. **Relational data:** URLs -> Snapshots -> Diffs -> Notifications is inherently relational.
2. **JSONB:** PostgreSQL JSONB provides document flexibility when needed.
3. **Transactions:** ACID guarantees for URL state changes.
4. **Full-text search:** PostgreSQL has built-in full-text search for URL names/tags.
5. **Mature tooling:** Alembic migrations, SQLAlchemy, excellent ORM support.

---

## 21. RISKS & MITIGATIONS

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Target sites block polling | High | High | Rotate user agents, respect robots.txt, implement backoff, use Playwright for JS pages |
| Storage growth | Medium | High | Snapshot pruning, S3 lifecycle policies, compression |
| IP bans from aggressive polling | High | Medium | Rate limiting, adaptive intervals, per-URL throttling |
| Diff quality poor | High | Medium | Multiple extraction methods, semantic diffing, user feedback loop |
| JS-heavy pages fail to render | Medium | Medium | Playwright integration, configurable per URL, fallback to raw HTML |
| Security vulnerability in stored HTML | High | Medium | HTML sanitization, CSP headers, DOMPurify, no inline scripts |
| Scale beyond monolith | Medium | Low | Clear module boundaries, extract polling worker first |
| API rate limits from targets | Medium | High | Exponential backoff, retry logic, user-configurable delays |

---

## 22. COST ESTIMATES

### 22.1 Development Phase (Self-Hosted)

| Component | Cost |
|-----------|------|
| VPS (4GB RAM, 2 vCPU) | $20-40/month |
| PostgreSQL (on VPS) | Included |
| Redis (on VPS) | Included |
| MinIO (on VPS) | Included |
| Domain + SSL | $10-15/year |
| **Total** | **$20-40/month** |

### 22.2 Production SaaS

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
| **Total** | **$150-250/month** |

### 22.3 Scale Production

| Component | Cost |
|-----------|------|
| Kubernetes (EKS/GKE) | $100-200/month |
| PostgreSQL (Multi-AZ) | $200-400/month |
| ElastiCache Redis | $50-100/month |
| S3 + CloudFront | $50-100/month |
| ECS/EKS compute | $300-500/month |
| **Total** | **$700-1200/month** |

---

## END OF DOCUMENT

This architecture document provides a comprehensive blueprint for building Emily Web Delta — a web page change monitoring platform. The recommended approach is a **Python/FastAPI modular monolith** with **Celery workers** for polling, **PostgreSQL** for storage, **React** for the frontend, and **diff2html** for diff display. The system is designed to scale from a single VPS ($20/month) to a Kubernetes cluster ($2000+/month) with clear decomposition paths.

The key differentiator is the **content extraction + semantic diff pipeline** — extracting meaningful text from HTML and computing paragraph-level diffs rather than line-level HTML diffs. This is where Python's ecosystem provides a decisive advantage.
