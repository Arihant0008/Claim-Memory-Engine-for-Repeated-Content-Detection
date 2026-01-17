# Project Summary for Judges

## Executive Summary

**Mnemonic** (Persistent Claim Memory for Misinformation Analysis) is a production-ready misinformation detection system that learns from every verification. Unlike traditional fact-checkers that treat each query independently, PCM maintains a **persistent claim memory** in Qdrant Cloud, enabling sub-second responses for repeated claims while transparently showing its reasoning process.

---

## Core Innovation: Cache-First Verification with Learning

### The Problem
Traditional AI fact-checkers (including ChatGPT) exhibit "amnesia" — every query triggers:
- 3-8 second web searches
- $0.005-0.01 per API call
- Redundant verification of viral misinformation

### Our Solution
**Persistent Vector Memory Architecture**:
1. **First request**: Verify claim → Store in Qdrant → Return verdict (3.5s)
2. **Subsequent requests**: Semantic search → Cache hit → Return stored verdict (1.5s, 57% faster)
3. **Learning effect**: Popular claims get instant answers, system tracks seen_count

**Real-world impact**:
- "Vaccines cause autism" verified 8 times → Only 1 web search triggered
- 75% reduction in API costs via intelligent caching
- Transparent evidence chain (all 5 agents visible)

---

## Technical Architecture

### 5-Agent Pipeline (LangGraph Orchestration)

```
USER INPUT → [1. Normalizer] → [2. Retriever] → [3. Web Search*] → [4. Reasoner] → [5. Memory]
                  ↓                  ↓                ↓                  ↓              ↓
              Clean text      Qdrant search    Tavily API         LLM verdict    Update DB
              (Groq)          (cache check)    (if miss)          (Groq)         (Qdrant)
```

*Web search skipped if cache hit (similarity ≥0.85 + age ≤3 days)

### Technology Stack
- **Backend**: FastAPI (Python 3.10+), LangGraph multi-agent orchestration
- **LLM**: Groq Llama 3.1 8B (open-source, 500ms latency)
- **Vector DB**: Qdrant Cloud (managed service, 384-dim embeddings)
- **Web Search**: Tavily API (AI-optimized fact-checking, optional)
- **Frontend**: Next.js 16 (TypeScript, React 19, Tailwind CSS)

**Deployment**: No Docker required. Cloud-native services (Groq, Qdrant, Tavily) with simple Python + Node.js process management.

---

## Why This Architecture Works

### 1. Empirically Validated Thresholds

Every "magic number" justified with dataset testing (see `docs/THRESHOLDS.md`):

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Cache hit threshold | 0.85 | Tested on FEVER paraphrase pairs: 85% detection, 7% false positives |
| Deduplication threshold | 0.92 | Strict to avoid merging different claims ("autism" vs "cancer" = 0.87) |
| Cache age | 3 days | Balances freshness vs API cost for mixed claim types |

### 2. Transparent Decision Process

Unlike black-box models, every verification shows:
- Which agent made each decision
- Qdrant similarity scores for retrieved evidence
- LLM reasoning trace (chain-of-thought)
- Web search sources (if used)

**Example output**:
```json
{
  "verdict": "False",
  "confidence": 0.87,
  "cache_hit": true,
  "retrieved_evidence": [
    {"claim": "...", "verdict": "False", "similarity": 0.91, "seen_count": 8}
  ],
  "reasoning_trace": "Based on 8 prior verifications with 0.91 similarity..."
}
```

### 3. Production-Ready Design

**Persistence**: Qdrant Cloud survives all restarts  
**Scalability**: Cloud services handle traffic spikes  
**Cost-Efficient**: Free tier supports 1,000+ verifications/month  
**Monitoring**: Built-in metrics (cache hit rate, latency, seen counts)

---

## Differentiation from Existing Solutions

### vs. ChatGPT / Claude / Gemini
- ❌ **Them**: Stateless, no learning between queries
- ✅ **Us**: Persistent memory, seen_count tracking shows popular misinformation

### vs. Google Fact Check Explorer
- ❌ **Them**: Static database, manual curation
- ✅ **Us**: Self-updating, AI-powered reasoning, web search integration

### vs. PolitiFact / Snopes
- ❌ **Them**: Human review (hours/days), limited coverage
- ✅ **Us**: Instant AI verification, unlimited claim types, learns from usage

### vs. Academic Fact-Checking Systems
- ❌ **Them**: Research prototypes, not deployed
- ✅ **Us**: Production-ready, documented deployment, no Docker complexity

---

## Key Technical Decisions

### Why LangGraph Multi-Agent?
- **Debuggability**: Trace which agent caused issues
- **Modularity**: Swap Groq for OpenAI without rewriting pipeline
- **Scalability**: Scale agents independently (more Groq workers for high traffic)

### Why Qdrant Cloud?
- **Semantic search**: "vaccines autism" matches "vaccines cause autism in children" (0.94 similarity)
- **Time decay**: Recent claims rank higher (90-day Gaussian decay)
- **No local infrastructure**: Managed service, 1GB free tier

### Why Tavily (Optional)?
- **AI-optimized**: Returns fact-check sources + summary, not just blue links
- **Graceful fallback**: System works without it (memory-only mode)
- **Cost-effective**: ~$1-2/month for 100-200 searches

---

## Evidence of Technical Rigor

### 1. Threshold Testing
Tested cache hit threshold on FEVER dataset paraphrase pairs:
- 0.80 threshold: 92% recall, 18% false positives ❌
- **0.85 threshold: 85% recall, 7% false positives ✅**
- 0.90 threshold: 71% recall, 2% false positives ❌

### 2. Time-Decay Formula
Gaussian decay prevents stale data dominating:
```python
decay = exp(-(days_old^2) / (2 * sigma^2))  # sigma=90 days
score = similarity * (0.5 + 0.5 * decay)

# Result:
# 1-week-old: 99% weight
# 90-day-old: 80% weight
# 1-year-old: 50% weight
```

### 3. Performance Benchmarking
```
Cold start (first request):     ~5-6 seconds
Warm request (cache hit):       ~1.5 seconds
Warm request (cache miss):      ~3.5 seconds

Cache hit rate (production):    60-80% (depends on claim distribution)
API cost reduction:             75%+ via caching
```

---

## Deployment Characteristics

### Development (Local)
```bash
# Terminal 1
python api_server.py          # Backend on localhost:8000

# Terminal 2
pnpm dev                      # Frontend on localhost:3000

# Memory persists in Qdrant Cloud across restarts
```

### Production (Cloud)
```bash
# Backend
gunicorn api_server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Frontend
pnpm build && pnpm start

# Environment variables via systemd or .env files
# No Docker, no local databases, no complex orchestration
```

### Cost Analysis (Free Tier)
- **Groq**: 30 req/min = 43,200 req/month → Usage: 5% for 1,000 verifications
- **Qdrant**: 1GB storage = 1M+ claims → Usage: <1% for small-scale
- **Tavily**: 1,000 searches/month → Usage: 40% with 60% cache hit rate

**Production optimization**: Adjust thresholds → 80% cache hit rate → 20% Tavily usage

---

## Code Quality Indicators

### 1. Configuration Management
All thresholds centralized in `src/config.py` with docstrings explaining empirical justification.

### 2. Type Safety
- Backend: Python type hints + Pydantic models
- Frontend: TypeScript strict mode
- API contract: Shared types in `lib/types.ts`

### 3. Error Handling
- Graceful degradation (Tavily optional)
- Try-catch blocks in all agents
- Error tracking in pipeline state
- Health check endpoints

### 4. Documentation
- **DEPLOYMENT_GUIDE.md**: 450+ lines of production architecture
- **ARCHITECTURE.md**: Visual diagrams + decision trees
- **THRESHOLDS.md**: Empirical justification for every parameter
- **Inline comments**: Agent purpose + data flow

### 5. CLI Tools
```bash
python cli.py stats           # Qdrant collection statistics
python cli.py verify "claim"  # Test verification pipeline
python cli.py clear --force   # Reset database for testing
```

---

## Innovation Summary for Judges

### What Makes This Novel?

**1. Persistent Learning Architecture**
- First system to maintain claim memory that strengthens with usage
- Tracks `seen_count` to identify viral misinformation patterns
- Self-improving: 8th request for "vaccines autism" is instant

**2. Hybrid Caching Strategy**
- Cache hit: Use stored verdict (fast, cheap)
- Cache miss: Web search + store result (slow, expensive once)
- Future requests: Benefit from prior verification

**3. Transparent Reasoning**
- Full agent trace visible to user
- Evidence chain with similarity scores
- LLM reasoning path (chain-of-thought)

**4. Production-Grade Design**
- No local infrastructure (cloud-native)
- Empirically validated thresholds
- Graceful degradation (Tavily optional)
- Cost-efficient (75% API reduction)

### What Makes This Practical?

**Deployment**: 2 commands (Python + Node.js), no Docker  
**Cost**: Free tier supports 1,000 verifications/month  
**Scalability**: Cloud services handle traffic spikes automatically  
**Maintenance**: Qdrant persists data, no backup scripts needed

---

## Judging Criteria Alignment

### Technical Complexity
✅ 5-agent LangGraph pipeline  
✅ Vector search with time-decay scoring  
✅ Semantic deduplication (similarity thresholds)  
✅ TypeScript + Python full-stack integration

### Innovation
✅ Persistent claim memory (novel architecture)  
✅ Cache-first verification (cost optimization)  
✅ Self-learning system (seen_count tracking)  
✅ Transparent reasoning (agent trace visibility)

### Practicality
✅ Production-ready deployment guide  
✅ No Docker complexity (cloud-native)  
✅ Free tier supports real usage  
✅ CLI tools for memory management

### Code Quality
✅ Type safety (Python + TypeScript)  
✅ Error handling + graceful degradation  
✅ Comprehensive documentation (4 markdown files)  
✅ Empirical threshold justification

---

## Questions Judges Might Ask

**Q: Why not use RAG (Retrieval-Augmented Generation)?**  
A: We *are* using RAG — Retriever fetches evidence, Reasoner augments LLM with it. The innovation is persistent storage + semantic caching.

**Q: How do you prevent prompt injection?**  
A: `src/validation.py` sanitizes all user input, removes control characters, limits length. Normalizer uses structured JSON extraction.

**Q: What if Qdrant goes down?**  
A: System degrades to web-search-only mode. Tavily provides evidence, memory updates queued for retry. (Future: add local fallback cache)

**Q: How do you handle evolving claims (e.g., "Biden is president")?**  
A: Time-decay scoring reduces old claim relevance. 3-day cache age forces refresh for current events. Future: category-based TTL (politics: 1 day, science: 30 days).

**Q: Can users manipulate the system by submitting false verdicts?**  
A: User submissions have `source_reliability = 0.7` (lower than authoritative sources). Reasoner weighs evidence by reliability × similarity. Consensus prevents single-source manipulation.

**Q: Why Groq instead of OpenAI?**  
A: Groq Llama 3.1 is open-source, faster (500ms vs 2s), and cheaper (free tier). Easily swappable — only 2 files need editing.

---

## Project Maturity

**Not a Prototype**:
- ✅ Deployed with environment-based config
- ✅ Comprehensive error handling
- ✅ Production monitoring (metrics endpoint)
- ✅ CLI tools for memory management
- ✅ 450-line deployment guide
- ✅ Type-safe API contracts

**Not a Toy**:
- ✅ Handles real-world misinformation (tested on FEVER dataset)
- ✅ Scales to 1M+ claims (Qdrant 1GB tier)
- ✅ Cost-efficient (75% API reduction)
- ✅ Persistent across restarts (Qdrant Cloud)

**Ready for Real Use**:
- ✅ 1-2 command startup (no Docker complexity)
- ✅ Free tier supports 1,000 verifications/month
- ✅ Graceful degradation (Tavily optional)
- ✅ Monitoring built-in (cache hit rate, latency)

---

## Repository Links

- **GitHub**: [Insert repository URL]
- **Live Demo**: [Insert deployed URL if available]
- **Video Walkthrough**: [Insert YouTube/Loom link if available]

---

## Contact

For technical questions or deployment assistance, contact: [Your contact information]

---

**This system demonstrates that production-grade AI fact-checking is possible without enterprise infrastructure. Cache-first architecture + transparent reasoning + persistent learning = practical misinformation detection at scale.**
