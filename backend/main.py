from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import shutil
import os
import sys
import tempfile
import glob

# Reuse logic from our library script
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# Docker support: Use environment variable for Ollama URL
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

from fastapi.middleware.cors import CORSMiddleware

# Import our auth and database modules
import models
import schemas
from database import engine, get_db
from auth import get_password_hash, authenticate_user, create_access_token, get_current_user

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG PDF Expert API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GLOBAL STATE
# In a real app, use a proper database or cache.
# For local dev, a global var is fine.
state = {
    "vector_db": None
}

DATA_FOLDER = "data_uploaded"
os.makedirs(DATA_FOLDER, exist_ok=True)

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[dict]

INDEX_FOLDER = "faiss_index"

@app.on_event("startup")
async def startup_event():
    """
    On startup, load the existing FAISS index if it exists.
    """
    global state
    if os.path.exists(INDEX_FOLDER):
        print("Loading existing vector store from disk...")
        embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
        try:
            state["vector_db"] = FAISS.load_local(INDEX_FOLDER, embeddings, allow_dangerous_deserialization=True)
            print("Vector store loaded successfully.")
        except Exception as e:
            print(f"Failed to load vector store: {e}")
    else:
        print("No existing vector store found. Starting fresh.")

from fastapi import BackgroundTasks

@app.post("/upload")
async def upload_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Accepts PDF uploads, saves them, and incrementally adds them to the vector index in the background.
    """
    global state
    new_files_paths = []

    # 1. Save uploaded files to disk
    for file in files:
        file_path = os.path.join(DATA_FOLDER, file.filename)
        # Check if file already exists to avoid re-processing perfectly identical uploads if desired,
        # but technically we should allow overwrites. 
        # For simplicity, we just overwrite and add to index (duplicates in index possible 
        # but user can manage files). Ideally we'd check hash.
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        new_files_paths.append(file_path)

    # 2. Process ONLY the new files
    if not new_files_paths:
        return {"status": "success", "message": "No new files uploaded."}

    # Run processing in background to avoid timeout
    background_tasks.add_task(process_new_files, new_files_paths)

    return {"status": "success", "message": f"Upload accepted. Processing {len(new_files_paths)} files in background."}

def process_new_files(file_paths: List[str]):
    import sys
    global state
    new_docs = []

    print(f"Processing {len(file_paths)} new files...")
    sys.stdout.flush()

    for pdf_file in file_paths:
        try:
            print(f"Loading {pdf_file}...")
            loader = PyPDFLoader(pdf_file)
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = os.path.basename(pdf_file)
            new_docs.extend(docs)
            print(f"Successfully loaded {len(docs)} pages from {pdf_file}")
            sys.stdout.flush()
        except Exception as e:
            print(f"Error loading {pdf_file}: {e}")
            import traceback
            traceback.print_exc()

    if not new_docs:
         print("ERROR: Could not extract text from uploaded files.")
         return {"status": "error", "message": "Could not extract text from uploaded files."}

    # Split
    print(f"Splitting {len(new_docs)} documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    chunks = splitter.split_documents(new_docs)
    print(f"Created {len(chunks)} chunks")
    sys.stdout.flush()

    # Embed & Index - Process in batches to handle large PDFs
    try:
        print("Creating embeddings...")
        embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
        
        # Process in batches of 100 chunks to avoid timeout/memory issues
        batch_size = 100
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        if state["vector_db"] is None:
            # Create new index with first batch
            print(f"Creating new vector store (processing {len(chunks)} chunks in {total_batches} batches)...")
            first_batch = chunks[:batch_size]
            vector_db = FAISS.from_documents(first_batch, embeddings)
            state["vector_db"] = vector_db
            print(f"Batch 1/{total_batches} complete")
            
            # Add remaining batches
            for i in range(batch_size, len(chunks), batch_size):
                batch_num = (i // batch_size) + 1
                batch = chunks[i:i + batch_size]
                state["vector_db"].add_documents(batch)
                print(f"Batch {batch_num}/{total_batches} complete")
        else:
            # Add to existing index in batches
            print(f"Adding to existing vector store ({len(chunks)} chunks in {total_batches} batches)...")
            for i in range(0, len(chunks), batch_size):
                batch_num = (i // batch_size) + 1
                batch = chunks[i:i + batch_size]
                state["vector_db"].add_documents(batch)
                print(f"Batch {batch_num}/{total_batches} complete")

        # Save to disk
        print("Saving vector store to disk...")
        state["vector_db"].save_local(INDEX_FOLDER)
        print(f"SUCCESS: Added {len(file_paths)} files ({len(chunks)} chunks) to the index.")
        sys.stdout.flush()
    except Exception as e:
        print(f"ERROR during indexing: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Indexing failed: {str(e)}"}
    
    return {"status": "success", "message": f"Added {len(file_paths)} files ({len(chunks)} chunks) to the index."}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    print("--- ENTERING CHAT ENDPOINT ---")
    try:
        if state["vector_db"] is None:
            raise HTTPException(status_code=400, detail="No documents indexed. Please upload files first.")
        
        vector_db = state["vector_db"]
        llm = ChatOllama(model="mistral", base_url=OLLAMA_BASE_URL)

        # 1. Retrieve - Increased to 40 chunks for comprehensive evidence gathering
        print("Retrieving docs...")
        docs_and_scores = vector_db.similarity_search_with_score(request.question, k=40)
        docs_and_scores.sort(key=lambda x: x[1])
        source_docs = [doc for doc, score in docs_and_scores]

        # 2. Context - Format as numbered source passages
        context_parts = []
        for idx, d in enumerate(source_docs, 1):
            src = d.metadata.get("source", "Unknown")
            pg = d.metadata.get("page", 0) + 1
            context_parts.append(f"Passage {idx} [{src}, p.{pg}]:\n{d.page_content}")
        context = "\n\n---\n\n".join(context_parts)
        
        # Debug: Log what we're sending to the AI
        print(f"Retrieved {len(source_docs)} passages")
        print(f"Context length: {len(context)} characters")
        print(f"First passage preview: {context[:500]}...")
        sys.stdout.flush()

        # 3. Prompt - Advanced research assistant with reasoning
        prompt = f"""You are an expert research assistant analyzing religious and historical texts.

Your task: Answer the user's question using intelligent reasoning based on the passages below.

FIRST: Check if the passages are relevant to the question. If they don't contain information about the question, say so clearly and stop.

ANSWER STRUCTURE (only if passages are relevant):

1. **Direct Answer**: Start with a clear, direct response to the question.

2. **Evidence & Analysis**: 
   - Quote relevant passages: "exact text" [Source, p.XX]
   - Explain what the quotes mean in your own words
   - Connect multiple pieces of evidence logically
   - Note any patterns, themes, or relationships

3. **Synthesis**:
   - Provide a comprehensive answer that combines evidence with reasoning
   - Paraphrase concepts while citing sources
   - If evidence conflicts, acknowledge both perspectives
   - If gaps exist, state what's missing

CRITICAL RULES:
✓ If passages don't answer the question, say: "The provided texts do not contain information about [topic]. Would you like me to provide general knowledge about this topic instead?"
✓ DO NOT summarize irrelevant passages
✓ Ground all claims in the provided passages with citations
✓ Use reasoning to connect ideas, but cite your evidence
✓ Paraphrase is encouraged, but always cite the source
✓ If you must use external knowledge, clearly state: "⚠️ Note: The following is based on general knowledge, not the provided texts: [your answer]. This may not reflect the specific perspective of these documents."

Question: {request.question}

Passages:
{context}

Your answer:""".strip()

        # 4. Infer
        print("Invoking LLM (Sync)...")
        # Direct sync invoke - FastAPI runs `def` endpoints in a threadpool
        response = llm.invoke(prompt)
        print("LLM Finished.")
        answer_text = response.content

        # 5. Format Citations - Only include sources actually cited in the response
        citations = []
        for d, score in docs_and_scores:
            source_name = d.metadata.get("source", "Unknown")
            page_num = d.metadata.get("page", 0) + 1
            
            # Check if this source was actually referenced in the answer
            # Look for patterns like "[source, p.XX]" or "source, p.XX"
            if source_name.replace('.pdf', '') in answer_text or f"p.{page_num}" in answer_text:
                citations.append({
                    "source": source_name,
                    "page": page_num,
                    "score": float(score),
                    "text": d.page_content
                })

        return ChatResponse(answer=answer_text, citations=citations)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Chat Error: {str(e)}\n"
        import traceback
        traceback_str = traceback.format_exc()
        print(error_msg)
        print(traceback_str)
        
        # Write to file to ensure we catch it
        with open("backend_error.log", "w") as f:
            f.write(error_msg)
            f.write(traceback_str)
            
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/list-documents")
def list_documents():
    """
    Returns a list of all uploaded PDF files in the database.
    """
    import os
    files = []
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.endswith('.pdf'):
                filepath = os.path.join(DATA_FOLDER, filename)
                file_size = os.path.getsize(filepath)
                files.append({
                    "filename": filename,
                    "size_mb": round(file_size / (1024 * 1024), 2)
                })
    return {"documents": files, "total": len(files)}

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        initials=user.initials
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create user-specific directories
    user_dir = os.path.join("data", "users", str(new_user.id))
    os.makedirs(os.path.join(user_dir, "documents"), exist_ok=True)
    os.makedirs(os.path.join(user_dir, "vector_store"), exist_ok=True)
    
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ============================================================================
# USER DATA ENDPOINTS
# ============================================================================

@app.get("/chat/history", response_model=List[schemas.ChatMessageResponse])
def get_chat_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get user's chat history, most recent first."""
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id
    ).order_by(models.ChatMessage.timestamp.desc()).limit(limit).all()
    
    return list(reversed(messages))  # Return in chronological order

@app.get("/documents", response_model=List[schemas.DocumentResponse])
def get_documents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of user's uploaded documents."""
    documents = db.query(models.Document).filter(
        models.Document.user_id == current_user.id
    ).order_by(models.Document.upload_date.desc()).all()
    
    return documents
