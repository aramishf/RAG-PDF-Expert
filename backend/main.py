from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import shutil
import os
import tempfile
import glob

# Reuse logic from our library script
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

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
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        try:
            state["vector_db"] = FAISS.load_local(INDEX_FOLDER, embeddings, allow_dangerous_deserialization=True)
            print("Vector store loaded successfully.")
        except Exception as e:
            print(f"Failed to load vector store: {e}")
    else:
        print("No existing vector store found. Starting fresh.")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Accepts PDF uploads, saves them, and incrementally adds them to the vector index.
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

    return await process_new_files(new_files_paths)

async def process_new_files(file_paths: List[str]):
    global state
    new_docs = []

    print(f"Processing {len(file_paths)} new files...")

    for pdf_file in file_paths:
        try:
            loader = PyPDFLoader(pdf_file)
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = os.path.basename(pdf_file)
            new_docs.extend(docs)
        except Exception as e:
            print(f"Error loading {pdf_file}: {e}")

    if not new_docs:
         return {"status": "error", "message": "Could not extract text from uploaded files."}

    # Split
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    chunks = splitter.split_documents(new_docs)

    # Embed & Index
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    if state["vector_db"] is None:
        # Create new index
        print("Creating new vector store...")
        vector_db = FAISS.from_documents(chunks, embeddings)
        state["vector_db"] = vector_db
    else:
        # Add to existing index
        print("Adding to existing vector store...")
        state["vector_db"].add_documents(chunks)

    # Save to disk
    state["vector_db"].save_local(INDEX_FOLDER)
    
    return {"status": "success", "message": f"Added {len(file_paths)} files ({len(chunks)} chunks) to the index."}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if state["vector_db"] is None:
        raise HTTPException(status_code=400, detail="No documents indexed. Please upload files first.")
    
    vector_db = state["vector_db"]
    llm = ChatOllama(model="llama3")

    # 1. Retrieve - Increased to 20 chunks for more comprehensive answers
    docs_and_scores = vector_db.similarity_search_with_score(request.question, k=20)
    docs_and_scores.sort(key=lambda x: x[1])
    source_docs = [doc for doc, score in docs_and_scores]

    # 2. Context
    context_parts = []
    for d in source_docs:
        src = d.metadata.get("source", "Unknown")
        pg = d.metadata.get("page", 0) + 1
        context_parts.append(f"[{src}, p.{pg}] {d.page_content}")
    context = "\n\n".join(context_parts)

    # 3. Prompt
    prompt = f"""
You are an expert research assistant with deep knowledge helping users analyze and understand content from a library of books.

Your task is to provide comprehensive, well-researched answers by:
1. Using your knowledge and analytical thinking to understand the question
2. Supporting EVERY claim with direct evidence and quotes from the provided books
3. Clearly distinguishing between what the books say and your analytical framework

RESPONSE STRUCTURE:
- Start with a clear, direct answer using your knowledge and reasoning
- IMMEDIATELY support each point with exact quotes from the books, citing Book Name and Page Number
- Provide detailed context and explanation around the evidence
- If making connections between ideas, base them on explicit textual evidence
- Include multiple relevant quotes from different sources when available

CRITICAL RULES:
1. ALWAYS cite exact quotes with [Book Name, p.XX] for every factual claim
2. Use your knowledge to provide thoughtful analysis, but ground it in textual evidence
3. Be comprehensive and detailed - this is research, not a summary
4. When quoting, use quotation marks and exact text from the source
5. If the books don't directly address something, say so clearly, then provide related information if available
6. Distinguish between what is explicitly stated vs. your analytical interpretation
7. Provide thorough explanations to help the user understand the material deeply

Question: {request.question}

Context from books:
{context}
""".strip()

    # 4. Infer
    response = llm.invoke(prompt)
    answer_text = response.content

    # 5. Format Citations
    citations = []
    for d, score in docs_and_scores:
        citations.append({
            "source": d.metadata.get("source", "Unknown"),
            "page": d.metadata.get("page", 0) + 1,
            "score": float(score),
            "text": d.page_content
        })

    return ChatResponse(answer=answer_text, citations=citations)

@app.get("/health")
def health():
    return {"status": "ok"}

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
