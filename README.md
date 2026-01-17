# Mnemonic - Persistent Claim Memory for Misinformation Analysis

Modern Next.js-powered misinformation detection system with persistent claim memory and multi-agent verification pipeline.

## 📖 Documentation Index

**New to the project?** Start here:
1. **[SETUP.md](SETUP.md)** - Step-by-step API key setup and troubleshooting
2. **[README.md](README.md)** (this file) - Quick start guide
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Visual diagrams and system flow

**For judges/reviewers:**
- **[JUDGE_SUMMARY.md](JUDGE_SUMMARY.md)** - Executive summary with innovation highlights

**For developers:**
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete production deployment architecture
- [docs/ARCHITECTURE_PROFESSIONAL.md](docs/ARCHITECTURE_PROFESSIONAL.md) - Technical deep dive
- [docs/THRESHOLDS.md](docs/THRESHOLDS.md) - Empirical justification for all parameters

---

## 🎯 Features

- **Real-time Misinformation Analysis**: Submit claims and get instant AI-powered verdicts
- **Persistent Memory**: Qdrant vector database stores verified claims with similarity search
- **Multi-Agent Pipeline**: 5-agent LangGraph system (Normalizer → Retriever → Web Search → Reasoner → Memory Updater)
- **Web Search Integration**: Optional Tavily API for fresh evidence gathering
- **Modern UI**: Next.js 16 with TypeScript, Tailwind CSS, and shadcn/ui components
- **System Monitoring**: Real-time backend health checks and status display

## 🏗️ Architecture

**Backend:**
- FastAPI server (port 8000)
- Groq Llama 3.1 8B for reasoning
- Qdrant Cloud vector database
- sentence-transformers/all-MiniLM-L6-v2 embeddings (384-dim)

**Frontend:**
- Next.js 16 (App Router)
- TypeScript + React 19
- Tailwind CSS + shadcn/ui
- Real-time API integration

## 📋 Prerequisites

- **Python**: 3.10+
- **Node.js**: 18+ (with pnpm)
- **API Keys**: 
  - Groq API key (required)
  - Qdrant Cloud credentials (required)
  - Tavily API key (optional, for web search)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Python backend
pip install -r requirements.txt

# Next.js frontend
pnpm install
```

### 2. Configure Environment

See **[SETUP.md](SETUP.md)** for detailed API key setup instructions.

```bash
# Copy and edit environment variables
cp .env.example .env
```

Edit `.env` with your API keys:
```env
GROQ_API_KEY=your_groq_key              # Required - Get from console.groq.com
QDRANT_URL=your_qdrant_url              # Required - Get from cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_key          # Required
TAVILY_API_KEY=your_tavily_key          # Optional - Get from tavily.com
```

Also configure frontend:
```bash
cp .env.example .env.local
```

### 3. Run the Application

**Terminal 1: Start Backend**
```bash
python api_server.py
```
Backend runs on `http://localhost:8000`

**Terminal 2: Start Frontend**
```bash
pnpm dev
```
Frontend runs on `http://localhost:3000`

## 📁 Project Structure

```
pmc-opus-anti/
├── api_server.py           # FastAPI backend server
├── cli.py                  # Command-line interface for memory management
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Main dashboard
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles
├── components/            # React UI components
│   ├── ui/               # shadcn/ui primitives
│   ├── claim-input.tsx
│   ├── decision-zone.tsx
│   ├── reasoning-evidence.tsx
│   ├── session-history.tsx
│   └── system-status.tsx
├── lib/                   # Frontend utilities
│   ├── api.ts            # Backend API client
│   ├── transform.ts      # Response transformers
│   └── types.ts          # TypeScript types
├── src/                   # Python backend
│   ├── config.py         # Configuration
│   ├── pipeline.py       # Main verification pipeline
│   ├── data_ingestion.py # Data loading
│   ├── validation.py     # Validation utilities
│   └── agents/           # LangGraph agents
│       ├── normalizer.py
│       ├── retriever.py
│       ├── web_search.py
│       ├── reasoner.py
│       └── memory.py
├── data/                  # Data storage
│   └── cache/            # Local cache
└── docs/                  # Documentation
    ├── ARCHITECTURE_SIMPLE.md
    ├── ARCHITECTURE_PROFESSIONAL.md
    └── THRESHOLDS.md
```

## 🔧 CLI Commands

Manage the memory database using the CLI:

```bash
# View memory statistics
python cli.py stats

# Clear all memory (with confirmation)
python cli.py clear

# Clear without confirmation
python cli.py clear --force

# Ingest claims from CSV
python cli.py ingest data/claims.csv
```

## 🌐 API Endpoints

**Backend (FastAPI)**
- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /verify` - Verify a claim
  ```json
  {
    "raw_text": "claim to verify"
  }
  ```

Full API documentation: `http://localhost:8000/docs`

## 🎨 Frontend Features

- **Claim Input**: Clean interface for submitting claims
- **Decision Zone**: Visual verdict display with confidence scores
- **Evidence Explorer**: View similar cached claims with similarity scores
- **Web Search Results**: Display fresh evidence from Tavily
- **Reasoning Trace**: Step-by-step agent decision pipeline
- **Session History**: Track all verifications in current session
- **System Status**: Real-time backend health monitoring

## 🔒 Memory Thresholds

- **Cache Hit**: 0.85 similarity + 3-day freshness window
- **Deduplication**: 0.92 similarity threshold
- **Time Decay**: 90-day sigma for freshness scoring

See [docs/THRESHOLDS.md](docs/THRESHOLDS.md) for details.

## 🧪 Development

```bash
# Frontend development
pnpm dev              # Start dev server with hot reload
pnpm build            # Build for production
pnpm start            # Start production server

# Backend development
python api_server.py  # Start FastAPI with auto-reload

# Type checking
cd src && mypy .      # Python type checking
```

## 🐛 Troubleshooting

**"API offline" error:**
- Ensure `api_server.py` is running
- Check `http://localhost:8000` is accessible
- Verify `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`

**Port conflicts:**
- Next.js: 3000 (change with `pnpm dev -p 3001`)
- FastAPI: 8000 (modify in `api_server.py`)

**CORS errors:**
- Backend pre-configured for `localhost:3000`
- Update CORS settings in `api_server.py` if using different port

**Memory not persisting:**
- Check Qdrant connection in `.env`
- Verify collection exists: `python cli.py stats`

## 📚 Documentation

### Quick Start
- **[JUDGE_SUMMARY.md](JUDGE_SUMMARY.md)** - Executive summary for judges/reviewers
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Visual diagrams and decision trees

### Technical Deep Dive
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete production architecture
- [Professional Architecture](docs/ARCHITECTURE_PROFESSIONAL.md) - Technical deep dive
- [Simple Architecture](docs/ARCHITECTURE_SIMPLE.md) - Beginner-friendly overview
- [Memory Thresholds](docs/THRESHOLDS.md) - Empirical justification for all parameters

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Built with:** FastAPI · Next.js · Groq · Qdrant · LangGraph · Tavily
