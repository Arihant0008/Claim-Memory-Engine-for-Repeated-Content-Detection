# Mnemonic - Persistent Claim Memory for Misinformation Analysis

Modern Next.js-powered misinformation detection system with persistent claim memory and multi-agent verification pipeline.

## � Repository Structure

```
pmc-opus-anti/
├── frontend/          # Next.js application → Deploy to Vercel
├── backend/           # FastAPI server → Deploy to Render
├── README.md          # This file
└── docs/              # Additional documentation
```

## 📖 Documentation Index

**New to the project?** Start here:
1. **[frontend/README.md](frontend/README.md)** - Frontend setup & Vercel deployment
2. **[backend/README.md](backend/README.md)** - Backend setup & Render deployment

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

**Communication:** Frontend → Backend via HTTP API with CORS configuration

## 📋 Prerequisites

- **Python**: 3.10+
- **Node.js**: 18+ (with pnpm)
- **API Keys**: 
  - Groq API key (required)
  - Qdrant Cloud credentials (required)
  - Tavily API key (optional, for web search)

## 🚀 Quick Start

### Local Development

**Terminal 1: Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Frontend**
```bash
cd frontend
pnpm install
cp .env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
pnpm dev
```

### Production Deployment

**1. Deploy Backend to Render**
- Root Directory: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
- Add environment variables (see [backend/README.md](backend/README.md))

**2. Deploy Frontend to Vercel**
- Root Directory: `frontend`
- Set `NEXT_PUBLIC_API_URL` to your Render backend URL
- Deploy (Vercel auto-detects Next.js)

**3. Update Backend CORS**
- Set `CORS_ORIGINS` in Render to your Vercel URL
- Redeploy backend

📖 **Detailed guide**: See [frontend/README.md](frontend/README.md) and [backend/README.md](backend/README.md)

### 2. Configure Environment

See **[SETUP.md](SETUP.md)** for detailed API key setup instructions.

**Backend Environment:**
```bash
# Copy and edit backend environment
cp .env.backend.example .env
```

Edit `.env` with your API keys:
```env
GROQ_API_KEY=your_groq_key              # Required - Get from console.groq.com
QDRANT_URL=your_qdrant_url              # Required - Get from cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_key          # Required
TAVILY_API_KEY=your_tavily_key          # Optional - Get from tavily.com
CORS_ORIGINS=http://localhost:3000      # Must match frontend URL
LOG_LEVEL=INFO                          # INFO for dev, WARNING for prod
```

**Frontend Environment:**
```bash
# Copy and edit frontend environment
cp .env.frontend.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend URL
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

### Split Deployment (Production)

For deploying frontend and backend to separate platforms:

1. **Deploy Backend** (Railway, Render, Fly.io)
   - See [BACKEND_README.md](BACKEND_README.md)
   - Note your backend URL (e.g., `https://api.example.com`)

2. **Deploy Frontend** (Vercel, Netlify)
   - See [FRONTEND_README.md](FRONTEND_README.md)
   - Set `NEXT_PUBLIC_API_URL` to your backend URL

3. **Update Backend CORS**
   - Set `CORS_ORIGINS` to your frontend URL
   - Redeploy backend

## 📁 Project Structure

```
pmc-opus-anti/
├── frontend/                  # Next.js Application
│   ├── app/                  # Next.js pages
│   ├── components/           # React components
│   ├── hooks/               # React hooks
│   ├── lib/                 # API client & utilities
│   ├── public/              # Static assets
│   ├── styles/              # CSS styles
│   ├── package.json
│   └── next.config.mjs
│
├── backend/                   # FastAPI Server
│   ├── api_server.py        # Entry point
│   ├── src/                 # Core logic
│   │   ├── pipeline.py      # Multi-agent pipeline
│   │   ├── agents/          # Agent implementations
│   │   └── config.py
│   ├── data/                # Runtime data
│   └── requirements.txt
│
└── docs/                     # Documentation
```

## 🌐 API Endpoints

**Backend (FastAPI)** - Default: http://localhost:8000
- `GET /health` - Health check
- `POST /verify` - Verify a claim

Full API documentation: `http://localhost:8000/docs`

## 📚 Frontend Features

- **Claim Input**: Clean interface for submitting claims
- **Decision Zone**: Visual verdict display with confidence scores
- **Evidence Explorer**: View similar cached claims
- **Web Search Results**: Display fresh evidence from Tavily
- **Reasoning Trace**: Step-by-step agent decisions
- **Session History**: Track all verifications
- **System Status**: Real-time backend health monitoring

## 🔒 Memory Thresholds

- **Cache Hit**: 0.85 similarity + 3-day freshness window
- **Deduplication**: 0.92 similarity threshold
- **Time Decay**: 90-day sigma for freshness scoring

See [docs/THRESHOLDS.md](docs/THRESHOLDS.md) for details.

## 🧪 Development

### Frontend
```bash
cd frontend
pnpm dev              # Start dev server with hot reload
pnpm build            # Build for production
pnpm start            # Start production server
```

### Backend
```bash
cd backend
uvicorn api_server:app --reload  # Start with auto-reload
```

## 🐛 Troubleshooting

**"API offline" error:**
- Ensure backend is running: `cd backend && uvicorn api_server:app --reload`
- Check `http://localhost:8000/health`
- Verify frontend `.env.local` has correct `NEXT_PUBLIC_API_URL`

**Port conflicts:**
- Frontend: 3000 (change with `pnpm dev -p 3001`)
- Backend: 8000 (change with `uvicorn api_server:app --port 8001`)

**CORS errors:**
- Update `CORS_ORIGINS` in backend `.env`
- Must match your frontend URL

**Import errors after restructure:**
- Frontend: All imports should be relative to `frontend/`
- Backend: All imports should work from `backend/` root

## 📚 Documentation

### Quick Start
- **[frontend/README.md](frontend/README.md)** - Frontend setup & deployment
- **[backend/README.md](backend/README.md)** - Backend setup & deployment
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture


## 📝 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Built with:** FastAPI · Next.js · Groq · Qdrant · LangGraph · Tavily ·
