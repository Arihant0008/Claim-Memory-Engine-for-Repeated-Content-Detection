# Environment Setup Quick Reference

## Required Environment Variables

Create a `.env` file in the project root with these values:

```bash
# ===================================
# REQUIRED - System will not work without these
# ===================================

# Groq API (LLM for reasoning)
# Get from: https://console.groq.com/keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

# Qdrant Cloud (Vector database)
# Get from: https://cloud.qdrant.io
QDRANT_URL=https://xxxxx.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# ===================================
# OPTIONAL - System works without these
# ===================================

# Tavily API (Web search)
# Get from: https://tavily.com
# If missing: System runs in memory-only mode
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxx
```

## Frontend Environment Variables

Create `.env.local` in the project root:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Getting API Keys

### 1. Groq API Key (Required - Free)
1. Visit https://console.groq.com
2. Sign up with email (no credit card)
3. Navigate to "API Keys" section
4. Click "Create API Key"
5. Copy the key starting with `gsk_`
6. **Free tier**: 30 requests/min, unlimited duration

### 2. Qdrant Cloud (Required - Free)
1. Visit https://cloud.qdrant.io
2. Sign up with email (no credit card)
3. Click "Create Cluster"
4. Select **Free tier** (1GB storage)
5. Choose region (e.g., us-east4-0)
6. Copy the cluster URL (format: `https://xxxxx.cloud.qdrant.io`)
7. Navigate to "Data Access Control"
8. Copy the API key
9. **Free tier**: 1GB storage (~1M claims), unlimited queries

### 3. Tavily API Key (Optional - Free)
1. Visit https://tavily.com
2. Sign up with email
3. Navigate to API dashboard
4. Copy API key starting with `tvly-`
5. **Free tier**: 1,000 searches/month
6. **Without Tavily**: System continues with memory-only mode (no web search)

## Verifying Setup

### Step 1: Check .env file exists
```bash
# Windows
type .env

# Linux/Mac
cat .env

# Should show your API keys
```

### Step 2: Test Groq connection
```bash
python -c "from groq import Groq; client = Groq(); print('✅ Groq connected')"
```

### Step 3: Test Qdrant connection
```bash
python cli.py stats
# Expected: Collection stats or "Creating collection" message
```

### Step 4: Test Tavily (optional)
```bash
python -c "from src.agents.web_search import WebSearchAgent; agent = WebSearchAgent(); print('✅ Tavily connected')"
# If this fails, system will print "⚠️ Web search disabled" on startup (OK)
```

### Step 5: Start system
```bash
# Terminal 1 - Backend
python api_server.py
# Look for:
# ✅ Web search enabled (Tavily)  [or ⚠️ Web search disabled]
# INFO:     Uvicorn running on http://127.0.0.1:8000

# Terminal 2 - Frontend
pnpm dev
# Look for:
# ○ Local: http://localhost:3000
```

### Step 6: Test end-to-end
1. Open http://localhost:3000
2. Check system status indicator (top right)
   - Should show green "Online" badge
3. Submit test claim: "The Earth is flat"
4. Verify response appears with verdict

## Common Setup Issues

### Issue: "Missing required environment variables"
**Cause**: `.env` file missing or incorrect format  
**Fix**:
```bash
# Copy example file
cp .env.example .env

# Edit with your API keys
# Windows: notepad .env
# Linux/Mac: nano .env
```

### Issue: "GROQ_API_KEY not found"
**Cause**: API key not set or typo in variable name  
**Fix**:
```bash
# Verify key exists in .env
grep GROQ_API_KEY .env

# Should output: GROQ_API_KEY=gsk_xxxxx
# If empty or wrong: Edit .env file
```

### Issue: "Qdrant connection timeout"
**Cause**: Incorrect URL or API key  
**Fix**:
```bash
# Test Qdrant URL (should respond)
curl https://YOUR_CLUSTER_URL.cloud.qdrant.io

# If fails: Check URL in Qdrant dashboard
# Ensure no trailing slash: ❌ https://xxx/ ✅ https://xxx
```

### Issue: "Tavily import error"
**Cause**: Package not installed  
**Fix**:
```bash
pip install tavily-python
```

**Alternative**: Remove `TAVILY_API_KEY` from `.env` to run without web search

### Issue: "Port 8000 already in use"
**Cause**: Another process using backend port  
**Fix**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Issue: "Port 3000 already in use"
**Cause**: Another process using frontend port  
**Fix**:
```bash
# Run on different port
pnpm dev -p 3001

# Update .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Issue: "Module not found" errors
**Cause**: Dependencies not installed  
**Fix**:
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
pnpm install
```

## Environment Variable Reference

### System Configuration (Optional Overrides)

Add these to `.env` to customize thresholds:

```bash
# Cache behavior
CACHE_HIT_THRESHOLD=0.85        # Default: 0.85 (range: 0.70-0.95)
CACHE_MAX_AGE_DAYS=3            # Default: 3 (range: 1-30)

# Deduplication
SIMILARITY_THRESHOLD=0.92       # Default: 0.92 (range: 0.85-0.98)

# Time decay
TIME_DECAY_SIGMA_DAYS=90        # Default: 90 (range: 30-365)

# Qdrant collection
COLLECTION_NAME=claims_memory   # Default: claims_memory
```

### Production Environment Template

```bash
# ===================================
# PRODUCTION .env TEMPLATE
# ===================================

# LLM API (Groq)
GROQ_API_KEY=gsk_production_key_here

# Vector Database (Qdrant Cloud)
QDRANT_URL=https://production-cluster.cloud.qdrant.io
QDRANT_API_KEY=production_qdrant_key_here

# Web Search (Tavily)
TAVILY_API_KEY=tvly_production_key_here

# Threshold Tuning (Optional)
CACHE_HIT_THRESHOLD=0.82       # Lower = more cache hits, less accuracy
CACHE_MAX_AGE_DAYS=7           # Higher = fewer web searches, staler data

# Security
# ⚠️ NEVER commit this file to git
# ⚠️ Use separate keys for dev/staging/prod
# ⚠️ Rotate keys quarterly
```

## Security Best Practices

### ✅ DO
- Use separate API keys for development and production
- Add `.env` to `.gitignore` (already done)
- Store production keys in secure vault (AWS Secrets Manager, HashiCorp Vault)
- Rotate API keys every 90 days
- Use read-only keys where possible
- Monitor API usage for anomalies

### ❌ DON'T
- Commit `.env` file to git
- Share API keys in Slack/Discord
- Use production keys for local testing
- Hardcode keys in source code
- Expose keys in frontend (use `NEXT_PUBLIC_*` only for non-sensitive values)

## Next Steps

After verifying setup:

1. **Test the system**: Submit various claims and observe behavior
2. **Check cache behavior**: Submit same claim twice, note latency difference
3. **Inspect memory**: Run `python cli.py stats` to see stored claims
4. **Read documentation**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment

---

**Need help?** See troubleshooting sections in:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) - Development issues
- [ARCHITECTURE.md](ARCHITECTURE.md#quick-start-commands) - CLI commands
- [README.md](README.md#troubleshooting) - Common errors
