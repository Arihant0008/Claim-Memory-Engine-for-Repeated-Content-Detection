# Command Reference Card

Quick reference for all Mnemonic commands.

## Development Commands

### Starting Services

```bash
# Option 1: Manual (2 terminals)
# Terminal 1 - Backend
python api_server.py

# Terminal 2 - Frontend
pnpm dev

# Option 2: Quick start script (Windows)
.\start.ps1

# Option 3: Quick start script (Linux/Mac)
./start.sh
```

### Stopping Services

```bash
# Press Ctrl+C in each terminal

# Or from start script: Press any key to stop
```

## Memory Management (CLI)

### View Statistics
```bash
# Show collection stats
python cli.py stats

# Expected output:
# ✅ Collection 'claims_memory' exists
#    Total claims: 42
#    Last updated: 2026-01-18 15:30:00
```

### Verify Claims
```bash
# Test single claim
python cli.py verify "The Earth is flat"

# With verbose output
python cli.py verify "Vaccines cause autism" --verbose
python cli.py verify "Vaccines cause autism" -v
```

### Clear Database
```bash
# Clear with confirmation prompt
python cli.py clear

# Force clear (no confirmation)
python cli.py clear --force
python cli.py clear -f
```

### Ingest Data
```bash
# Load claims from CSV
python cli.py ingest data/claims.csv

# Use only curated fallback claims
python cli.py ingest --curated-only
python cli.py ingest -c

# Use real HuggingFace datasets (default)
python cli.py ingest --real-datasets
python cli.py ingest -r
```

## Frontend Commands

### Development
```bash
# Start dev server with hot reload
pnpm dev

# Start on different port
pnpm dev -p 3001
```

### Production Build
```bash
# Build optimized bundle
pnpm build

# Start production server
pnpm start

# Build and start
pnpm build && pnpm start
```

### Linting
```bash
# Run ESLint
pnpm lint

# Fix auto-fixable issues
pnpm lint --fix
```

### Dependencies
```bash
# Install all packages
pnpm install

# Add new package
pnpm add <package-name>

# Add dev dependency
pnpm add -D <package-name>

# Update all packages
pnpm update
```

## Backend Commands

### Running Server

```bash
# Development (auto-reload)
python api_server.py

# Production (Uvicorn)
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 1

# Production (Gunicorn)
gunicorn api_server:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Testing Components

```bash
# Test Groq connection
python -c "from groq import Groq; client = Groq(); print('✅ Groq OK')"

# Test Qdrant connection
python -c "from src.agents.retriever import RetrievalAgent; r = RetrievalAgent(); print('✅ Qdrant OK')"

# Test Tavily connection
python -c "from src.agents.web_search import WebSearchAgent; w = WebSearchAgent(); print('✅ Tavily OK')"

# Test full pipeline
python -c "from src.pipeline import create_pipeline; p = create_pipeline(); print('✅ Pipeline OK')"
```

### Python Package Management

```bash
# Install all dependencies
pip install -r requirements.txt

# Install specific package
pip install <package-name>

# Freeze current environment
pip freeze > requirements-lock.txt

# Update requirements.txt
pip list --outdated
```

## Debugging Commands

### Check Environment Variables

```bash
# Windows - Check .env file
type .env
findstr "GROQ_API_KEY" .env

# Linux/Mac - Check .env file
cat .env
grep "GROQ_API_KEY" .env
```

### Port Management

```bash
# Windows - Check what's using port
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill process by PID
taskkill /PID <PID> /F

# Linux/Mac - Check port usage
lsof -i :8000
lsof -i :3000

# Kill process
kill -9 <PID>
```

### Check Running Services

```bash
# Test backend health
curl http://localhost:8000/
curl http://localhost:8000/health

# Test verification endpoint
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "The Earth is flat"}'

# Check frontend
curl http://localhost:3000
```

### View Logs

```bash
# Backend logs (if running in terminal)
# Already visible in stdout

# Frontend logs
# Already visible in stdout

# System logs (if using systemd)
sudo journalctl -u pmc-backend -f
sudo journalctl -u pmc-frontend -f
```

## Git Commands

### Basic Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push to remote
git push origin main

# Pull latest
git pull origin main
```

### Branch Management

```bash
# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main

# Merge branch
git merge feature/new-feature

# Delete branch
git branch -d feature/new-feature
```

### Undo Changes

```bash
# Discard local changes
git checkout -- <file>

# Unstage file
git reset HEAD <file>

# Revert last commit
git revert HEAD

# Reset to specific commit
git reset --hard <commit-hash>
```

## Process Management (Production)

### Using PM2

```bash
# Install PM2
npm install -g pm2

# Start frontend
pm2 start npm --name "pmc-frontend" -- start

# Start backend
pm2 start python --name "pmc-backend" -- api_server.py

# View logs
pm2 logs

# Monitor
pm2 monit

# Restart
pm2 restart all

# Stop
pm2 stop all

# Delete processes
pm2 delete all

# Save configuration
pm2 save

# Enable auto-start on boot
pm2 startup
```

### Using systemd (Linux)

```bash
# Check service status
sudo systemctl status pmc-backend
sudo systemctl status pmc-frontend

# Start service
sudo systemctl start pmc-backend

# Stop service
sudo systemctl stop pmc-backend

# Restart service
sudo systemctl restart pmc-backend

# Enable auto-start on boot
sudo systemctl enable pmc-backend

# View logs
sudo journalctl -u pmc-backend -f
```

## Database Commands

### Qdrant CLI (via Python)

```bash
# List all collections
python -c "from qdrant_client import QdrantClient; from src.config import QDRANT_URL, QDRANT_API_KEY; client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY); print(client.get_collections())"

# Count points in collection
python cli.py stats

# Delete collection
python -c "from qdrant_client import QdrantClient; from src.config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME; client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY); client.delete_collection(COLLECTION_NAME); print('Deleted')"
```

## Performance Testing

### Load Testing (Backend)

```bash
# Install Apache Bench
# Windows: Download from Apache
# Linux: sudo apt install apache2-utils
# Mac: brew install httpd

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/

# Test verification endpoint (POST)
# Create test.json: {"raw_text": "test claim"}
ab -n 100 -c 5 -p test.json -T application/json http://localhost:8000/verify
```

### Monitoring Performance

```bash
# Watch backend logs with timing
python api_server.py | grep "latency"

# Monitor memory usage
# Windows: Task Manager
# Linux/Mac: htop or top
```

## Backup & Restore

### Backup Qdrant Data

```bash
# Note: Qdrant Cloud handles backups automatically
# To export data for local backup:

python -c "
from src.agents.retriever import RetrievalAgent
import json

r = RetrievalAgent()
results = r.client.scroll(collection_name='claims_memory', limit=10000)
claims = [{'id': p.id, 'payload': p.payload, 'vector': p.vector} for p in results[0]]

with open('backup.json', 'w') as f:
    json.dump(claims, f, indent=2)

print(f'Backed up {len(claims)} claims')
"
```

### Restore from Backup

```bash
# Clear existing data
python cli.py clear --force

# Restore from backup.json
python -c "
from src.agents.memory import MemoryUpdateAgent
import json

with open('backup.json', 'r') as f:
    claims = json.load(f)

agent = MemoryUpdateAgent()
# Implement batch_restore method or loop through claims
"
```

## Useful Aliases

Add these to your `.bashrc` or `.zshrc` (Linux/Mac) or PowerShell profile (Windows):

```bash
# Start services
alias pmc-start="cd ~/pmc-opus-anti && python api_server.py"
alias pmc-frontend="cd ~/pmc-opus-anti && pnpm dev"

# CLI shortcuts
alias pmc-stats="python cli.py stats"
alias pmc-verify="python cli.py verify"
alias pmc-clear="python cli.py clear --force"

# Testing
alias pmc-test-backend="curl http://localhost:8000/health"
alias pmc-test-frontend="curl http://localhost:3000"
```

## Environment-Specific Commands

### Development
```bash
# Use .env.development
cp .env.example .env.development
export ENV=development  # Linux/Mac
set ENV=development     # Windows
```

### Staging
```bash
# Use .env.staging
cp .env.example .env.staging
export ENV=staging
```

### Production
```bash
# Use .env.production
cp .env.example .env.production
export ENV=production
```

## Quick Troubleshooting

```bash
# Backend not starting?
python -c "import sys; print(sys.version)"  # Check Python version
pip install -r requirements.txt             # Reinstall dependencies

# Frontend not building?
node --version                              # Check Node.js version
pnpm install --force                        # Clean reinstall

# Port conflicts?
# Windows
netstat -ano | findstr :8000
# Linux/Mac
lsof -i :8000

# Can't connect to Qdrant?
curl https://YOUR_CLUSTER_URL.cloud.qdrant.io

# Environment variables not loading?
# Windows
Get-Content .env
# Linux/Mac
cat .env | grep -v "^#"
```

---

**For detailed explanations, see:**
- [SETUP.md](SETUP.md) - API key setup
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
