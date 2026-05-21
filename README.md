# RAG PDF Expert

AI-powered document analysis system using Retrieval-Augmented Generation (RAG). Upload PDFs and ask questions about their content with intelligent, citation-backed answers.

## Features

- 📄 **PDF Upload & Processing**: Automatic text extraction and indexing
- 🤖 **AI-Powered Chat**: Ask questions and get intelligent answers with citations
- 🔍 **Semantic Search**: Find relevant passages across multiple documents
- 💾 **Persistent Storage**: Vector database saves your indexed documents
- 🎯 **Citation Tracking**: Every answer includes source references

## Quick Start with Docker (Recommended)

**Prerequisites:** Docker Desktop installed

```bash
# Clone the repository
git clone https://github.com/aramishf/RAG-PDF-Expert.git
cd RAG-PDF-Expert

# Start everything
docker-compose up

# Open browser
open http://localhost:3000
```

**First run:** Downloads Mistral model (~4GB, takes 5-10 minutes)

📖 **Full Docker guide:** See [DOCKER.md](./DOCKER.md)

---

## Manual Setup (Without Docker)

### Prerequisites
- Python 3.12+
- Node.js 20+
- Ollama ([Download](https://ollama.ai))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Ollama Setup

```bash
# Start Ollama service
ollama serve

# Download Mistral model
ollama pull mistral

# Download embedding model
ollama pull nomic-embed-text
```

---

## Usage

1. **Upload PDFs**: Click "Upload" and select your documents
2. **Wait for Processing**: Large files are processed in batches
3. **Ask Questions**: Type your question in the chat
4. **Get Answers**: AI provides answers with citations

### Example Questions

- "What is the main argument in this document?"
- "Summarize the key findings"
- "What evidence supports [specific claim]?"
- "Compare the perspectives on [topic]"

---

## Architecture

```
Frontend (Next.js) → Backend (FastAPI) → Ollama (Mistral)
                          ↓
                    FAISS Vector DB
```

**Tech Stack:**
- **Frontend**: Next.js, TypeScript, TailwindCSS
- **Backend**: FastAPI, Python
- **AI**: Ollama (Mistral model)
- **Vector DB**: FAISS
- **Embeddings**: nomic-embed-text

---

## Project Structure

```
RAG-PDF-EXPERT/
├── frontend/           # Next.js web application
│   ├── components/     # React components
│   ├── lib/           # API client
│   └── app/           # Next.js pages
├── backend/           # FastAPI server
│   ├── main.py        # Main application
│   ├── models.py      # Database models
│   └── requirements.txt
├── docker-compose.yml # Docker orchestration
└── DOCKER.md         # Docker guide
```

---

## Configuration

### Environment Variables

**Backend** (`.env`):
```bash
OLLAMA_BASE_URL=http://localhost:11434  # Ollama service URL
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API URL
```

---

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Format Python code
black backend/

# Lint TypeScript
cd frontend
npm run lint
```

---

## Troubleshooting

### "No documents indexed" error
- Ensure PDFs contain selectable text (not scanned images)
- Check backend logs for processing errors

### Chat not responding
- Verify Ollama is running: `ollama list`
- Check backend is running: `curl http://localhost:8000/health`

### Slow processing
- Large PDFs (>40MB) take time to process
- Check backend logs for batch processing progress

📖 **More help:** See [DOCKER.md](./DOCKER.md#troubleshooting)

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - see LICENSE file for details

---

## Acknowledgments

- Built with [LangChain](https://langchain.com)
- Powered by [Ollama](https://ollama.ai)
- UI inspired by modern chat interfaces

---

## Contact

**Author:** Aramish Farooq  
**GitHub:** [@aramishf](https://github.com/aramishf)  
**Project:** [RAG-PDF-Expert](https://github.com/aramishf/RAG-PDF-Expert)
