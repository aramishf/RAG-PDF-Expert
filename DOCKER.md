# 🐳 Docker Guide for RAG PDF Expert

## What You'll Learn
This guide teaches you how to run the RAG PDF Expert application using Docker. By the end, you'll understand:
- What Docker containers are
- How to run multi-service applications
- How data persists across container restarts

---

## Prerequisites

**Required:**
- Docker Desktop installed ([Download here](https://www.docker.com/products/docker-desktop))
- 10GB free disk space (for AI models)

**Check if Docker is installed:**
```bash
docker --version
docker-compose --version
```

---

## Quick Start (For Your Friend!)

**1. Clone the repository:**
```bash
git clone https://github.com/aramishf/RAG-PDF-Expert.git
cd RAG-PDF-Expert
```

**2. Start everything with ONE command:**
```bash
docker-compose up
```

**3. Wait for initialization:**
- First run downloads Mistral model (~4GB, takes 5-10 minutes)
- Watch the logs - you'll see "✅ Mistral model downloaded successfully!"

**4. Open your browser:**
```
http://localhost:3000
```

**That's it!** 🎉

---

## Understanding What Just Happened

### The Magic of `docker-compose up`

When you ran that command, Docker:

1. **Built 2 images** (frontend & backend)
   - Compiled your code into runnable packages
   
2. **Downloaded 1 image** (Ollama)
   - Official AI model server
   
3. **Created 3 containers**:
   - `rag-frontend`: Next.js web interface (port 3000)
   - `rag-backend`: FastAPI server (port 8000)
   - `rag-ollama`: AI model server (port 11434)
   
4. **Created 3 volumes** (persistent storage):
   - `ollama_models`: Stores Mistral model
   - `uploaded_data`: Stores your PDFs
   - `faiss_index`: Stores vector database

5. **Connected everything** via a Docker network

---

## Common Commands

### Start the application:
```bash
docker-compose up
```

### Start in background (detached mode):
```bash
docker-compose up -d
```

### Stop the application:
```bash
docker-compose down
```

### View logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs -f frontend  # -f = follow (live updates)
```

### Rebuild after code changes:
```bash
docker-compose up --build
```

### Remove everything (including data!):
```bash
docker-compose down -v  # -v removes volumes
```

---

## Troubleshooting

### "Port already in use"
**Problem:** Another app is using port 3000 or 8000

**Solution:**
```bash
# Find what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

### "Ollama model not downloading"
**Problem:** Network issues or disk space

**Solution:**
```bash
# Check Ollama logs
docker-compose logs ollama

# Manually download model
docker-compose exec ollama ollama pull mistral
```

### "Backend can't connect to Ollama"
**Problem:** Ollama not ready yet

**Solution:**
```bash
# Wait for health check to pass
docker-compose ps  # Check STATUS column

# Restart backend
docker-compose restart backend
```

### "Changes not appearing"
**Problem:** Docker using cached build

**Solution:**
```bash
# Force rebuild
docker-compose up --build --force-recreate
```

---

## How Data Persists

### Volumes Explained
Docker volumes are like external hard drives:

```
Your Computer          Docker Volume
    ↓                       ↓
Delete container    →   Data survives!
Restart Docker      →   Data survives!
```

**View your volumes:**
```bash
docker volume ls
```

**Inspect a volume:**
```bash
docker volume inspect rag-pdf-expert_uploaded_data
```

**Backup a volume:**
```bash
docker run --rm -v rag-pdf-expert_uploaded_data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz /data
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                  Your Computer                  │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │   Frontend   │  │   Backend    │  │ Ollama ││
│  │   (Next.js)  │  │  (FastAPI)   │  │  (AI)  ││
│  │              │  │              │  │        ││
│  │  Port 3000   │  │  Port 8000   │  │ 11434  ││
│  └──────┬───────┘  └──────┬───────┘  └───┬────┘│
│         │                 │               │     │
│         └─────────────────┴───────────────┘     │
│                Docker Network                   │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │           Docker Volumes                 │  │
│  │  • ollama_models (4GB)                   │  │
│  │  • uploaded_data (your PDFs)             │  │
│  │  • faiss_index (vector DB)               │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Development Workflow

### Making Code Changes

**Backend changes:**
```bash
# Edit backend/main.py
docker-compose restart backend
```

**Frontend changes:**
```bash
# Edit frontend/components/...
docker-compose up --build frontend
```

**Dependency changes:**
```bash
# Edit requirements.txt or package.json
docker-compose up --build
```

---

## Production Deployment

For production, consider:

1. **Environment variables:**
   - Create `.env.production`
   - Never commit secrets!

2. **Resource limits:**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

3. **Health checks:**
   - Already configured in docker-compose.yml

4. **Logging:**
   ```bash
   docker-compose logs > app.log
   ```

---

## Learning Resources

- [Docker Official Tutorial](https://docs.docker.com/get-started/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## Questions?

Common questions answered:

**Q: Why Docker?**
A: One command to run everything. No "works on my machine" problems.

**Q: Can I use this without Docker?**
A: Yes! See the main README.md for manual setup.

**Q: How much disk space?**
A: ~6GB (4GB for Mistral model, 2GB for images)

**Q: Is it slower than running locally?**
A: Negligible difference. Docker adds <5% overhead.
