# System Architecture Quick Reference

## Data Flow Diagram

```
┌─────────────┐
│   USER      │ Submits claim via Next.js UI (localhost:3000)
└──────┬──────┘
       │ HTTP POST /verify
       ▼
┌─────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                        │
│                   (localhost:8000)                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  LANGGRAPH PIPELINE (5 Sequential Agents)        │   │
│  │                                                   │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │ 1. NORMALIZER (Groq Llama 3.1)            │  │   │
│  │  │    Raw → Normalized text                   │  │   │
│  │  │    "Did u kno...?" → "Vaccines cause..."   │  │   │
│  │  └─────────────────┬─────────────────────────┘  │   │
│  │                    │                             │   │
│  │  ┌─────────────────▼─────────────────────────┐  │   │
│  │  │ 2. RETRIEVER (Qdrant Cloud)               │  │   │
│  │  │    Vector search for similar claims        │  │   │
│  │  │    Returns: Top-10 matches + similarity    │  │   │
│  │  │    Decision: Cache hit? (≥0.85 + <3 days)│  │   │
│  │  └─────────────────┬─────────────────────────┘  │   │
│  │                    │                             │   │
│  │            ┌───────┴────────┐                    │   │
│  │            │                │                    │   │
│  │     Cache Hit         Cache Miss                │   │
│  │            │                │                    │   │
│  │            │     ┌──────────▼──────────────┐    │   │
│  │            │     │ 3. WEB SEARCH (Tavily)  │    │   │
│  │            │     │    Fetch fresh evidence  │    │   │
│  │            │     │    5 fact-check sources  │    │   │
│  │            │     └──────────┬──────────────┘    │   │
│  │            │                │                    │   │
│  │            └────────┬───────┘                    │   │
│  │                     │                            │   │
│  │  ┌──────────────────▼──────────────────────┐    │   │
│  │  │ 4. REASONER (Groq Llama 3.1)            │    │   │
│  │  │    Analyze evidence → Verdict            │    │   │
│  │  │    Output: True/False/Uncertain + conf.  │    │   │
│  │  └─────────────────┬─────────────────────────┘   │   │
│  │                    │                             │   │
│  │  ┌─────────────────▼─────────────────────────┐  │   │
│  │  │ 5. MEMORY UPDATER (Qdrant Cloud)         │  │   │
│  │  │    Store/update verified claim            │  │   │
│  │  │    If duplicate (≥0.92): seen_count++    │  │   │
│  │  │    Else: Create new record                │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  │                                                   │   │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  Returns JSON: {verdict, confidence, evidence, ...}      │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Next.js UI  │ Display result to user
                    └─────────────┘
```

## External Services

```
┌─────────────────────────────────────────────────────────┐
│  EXTERNAL APIS (Cloud-Hosted)                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🧠 Groq API (Llama 3.1 8B)                             │
│     • Used by: Normalizer, Reasoner                      │
│     • Latency: ~500-800ms per call                       │
│     • Rate limit: 30 req/min (free tier)                 │
│                                                          │
│  🔍 Qdrant Cloud (Vector Database)                      │
│     • Used by: Retriever, Memory Updater                 │
│     • Latency: ~50-100ms per operation                   │
│     • Storage: 1GB free (1M+ claims)                     │
│     • Collection: claims_memory                          │
│     • Vectors: 384-dim (all-MiniLM-L6-v2)               │
│                                                          │
│  🌐 Tavily API (Web Search)                             │
│     • Used by: Web Searcher (conditional)                │
│     • Latency: ~1-3 seconds per search                   │
│     • Rate limit: 1,000 searches/month (free tier)       │
│     • Fallback: Graceful (memory-only mode)              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Cache Decision Logic

```
┌─────────────────────────────────────────────────┐
│  CACHE HIT DECISION TREE                        │
└─────────────────────────────────────────────────┘

User submits claim
      │
      ▼
Normalize text
      │
      ▼
Search Qdrant for similar claims
      │
      ├─ No matches found
      │       │
      │       └─► CACHE MISS → Web search
      │
      └─ Matches found (Top-10 retrieved)
              │
              ▼
         Best match similarity ≥ 0.85?
              │
              ├─ No → CACHE MISS → Web search
              │
              └─ Yes
                   │
                   ▼
              Claim age ≤ 3 days?
                   │
                   ├─ No → CACHE MISS → Web search (refresh stale)
                   │
                   └─ Yes → ✅ CACHE HIT (skip web search)
                                 │
                                 └─► Use cached evidence
                                      Increment seen_count
                                      Return verdict in <1.5s
```

## Memory Deduplication Logic

```
┌─────────────────────────────────────────────────┐
│  MEMORY UPDATE DEDUPLICATION                    │
└─────────────────────────────────────────────────┘

New verification complete
      │
      ▼
Search for near-duplicate in Qdrant
      │
      ├─ No match (similarity < 0.92)
      │       │
      │       └─► CREATE new record
      │            • seen_count = 1
      │            • timestamp = now
      │
      └─ Match found (similarity ≥ 0.92)
              │
              └─► UPDATE existing record
                   • seen_count++
                   • last_seen = now
                   • Update verdict if confidence higher
```

## Threshold Reference Card

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **CACHE_HIT_THRESHOLD** | 0.85 | Semantic similarity required for cache hit |
| **SIMILARITY_THRESHOLD** | 0.92 | Deduplication threshold (stricter) |
| **CACHE_MAX_AGE_DAYS** | 3 | Maximum age for cached verdicts |
| **TIME_DECAY_SIGMA** | 90 | Gaussian decay parameter (days) |
| **DEFAULT_TOP_K** | 10 | Number of similar claims retrieved |

**Why 0.85 vs 0.92?**
- **Cache hit (0.85)**: "Is this asking the same question?" → Flexible
- **Deduplication (0.92)**: "Is this the exact same record?" → Strict

## Performance Characteristics

### Cold Start (First Request)
```
Backend initialization: ~2-3 seconds
  ├─ Import agents
  ├─ Load embedding model
  └─ Connect to Qdrant

First verification: ~5-6 seconds total
```

### Warm Requests (Cache Hit)
```
Normalization:        ~500ms  (Groq API)
Qdrant search:        ~50ms   (Vector lookup)
Web search:           SKIPPED
Reasoning:            ~800ms  (Groq API, uses cache)
Memory update:        ~100ms  (Qdrant upsert)
─────────────────────────────────────────
Total latency:        ~1.5s   (57% faster)
```

### Warm Requests (Cache Miss)
```
Normalization:        ~500ms  (Groq API)
Qdrant search:        ~50ms   (No good match)
Web search:           ~2s     (Tavily API)
Reasoning:            ~800ms  (Groq API, uses web)
Memory update:        ~100ms  (Qdrant create)
─────────────────────────────────────────
Total latency:        ~3.5s
```

## Cost Analysis (Free Tier Limits)

### Monthly API Usage (1,000 verifications)
```
Groq API:
  • Cache hits (60%): 600 × 2 calls = 1,200 calls
  • Cache misses (40%): 400 × 2 calls = 800 calls
  • Total: 2,000 calls/month
  • Limit: 43,200 calls/month (30/min × 60min × 24hr × 30d)
  • Usage: 4.6% ✅

Qdrant Cloud:
  • All requests: 1,000 searches + 1,000 updates
  • Storage: ~5MB per 1,000 claims
  • Limit: 1GB storage, unlimited queries
  • Usage: 0.5% ✅

Tavily API:
  • Cache misses only: 400 searches
  • Limit: 1,000 searches/month
  • Usage: 40% ✅
```

**Optimization for higher traffic**:
- Increase `CACHE_HIT_THRESHOLD` to 0.82 → 75% cache hit rate
- Extend `CACHE_MAX_AGE_DAYS` to 7 → Reduce refreshes
- Result: 80% reduction in Tavily usage

## Environment Variables Reference

### Required
```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxx          # Llama 3.1 inference
QDRANT_URL=https://xxx.cloud.qdrant.io  # Vector database
QDRANT_API_KEY=xxxxxxxxxxxxx            # Qdrant authentication
```

### Optional
```bash
TAVILY_API_KEY=tvly_xxxxxxxxxxxxx       # Web search (graceful fallback)

# Threshold overrides (defaults shown)
CACHE_HIT_THRESHOLD=0.85
SIMILARITY_THRESHOLD=0.92
CACHE_MAX_AGE_DAYS=3
TIME_DECAY_SIGMA_DAYS=90
```

### Frontend
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API endpoint
```

## Quick Start Commands

```bash
# Development
python api_server.py              # Start backend (port 8000)
pnpm dev                          # Start frontend (port 3000)

# CLI Tools
python cli.py stats               # View memory statistics
python cli.py verify "claim text" # Test verification
python cli.py clear --force       # Clear database

# Production
gunicorn api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

pnpm build && pnpm start          # Build + serve frontend
```

## Directory Structure

```
pmc-opus-anti/
├── api_server.py           # FastAPI backend entry point
├── cli.py                  # Memory management CLI
├── DEPLOYMENT_GUIDE.md     # This comprehensive guide
│
├── app/                    # Next.js pages
│   ├── page.tsx           # Main dashboard
│   └── layout.tsx         # Root layout
│
├── components/             # React UI components
│   ├── claim-input.tsx
│   ├── decision-zone.tsx
│   └── system-status.tsx
│
├── lib/                    # Frontend utilities
│   ├── api.ts             # Backend API client
│   └── transform.ts       # Response transformers
│
└── src/                    # Python backend
    ├── pipeline.py        # LangGraph orchestration
    ├── config.py          # Configuration + thresholds
    └── agents/            # 5-agent system
        ├── normalizer.py
        ├── retriever.py
        ├── web_search.py
        ├── reasoner.py
        └── memory.py
```

---

**For complete deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**
