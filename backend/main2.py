# =============================================================================
# 1. IMPORTS
# Importing necessary libraries to build the RAG system
# =============================================================================
import os  # To check if files/folders exist on the computer
from dotenv import load_dotenv  # To load environment variables (not strictly needed for Ollama but good practice)
from langchain_ollama import ChatOllama, OllamaEmbeddings  # The AI components (Brain + Vectorizer)
from langchain_community.document_loaders import PyPDFLoader  # Tool to read PDF files
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Tool to cut text into small pieces
from langchain_community.vectorstores import FAISS  # The database specifically for storing vectors (Fast AI Similarity Search)

# Load existing environment variables (if any)
load_dotenv()

# =============================================================================
# 2. CONFIGURATION
# Settings for our specific book and system behavior
# =============================================================================
PDF_PATH = "data/Philosophy-of-Teachings-of-Islam.pdf"
# PAGE_OFFSET: Correction factor. 
# calculated as: (Printed_Page_Number) - (PDF_File_Page_Index)
# If PDF page 50 is physically printed as "10", offset is -40.
PAGE_OFFSET = -40  
# DB_PATH: Folder name on your computer where we save the "learned" book data
DB_PATH = "faiss_index_fast"

def start_rag():
    print("Initializing RAG (Fast Mode)...")
    
    # =============================================================================
    # 3. SETTING UP THE "READER" (Embeddings)
    # =============================================================================
    # We use 'nomic-embed-text' here instead of 'llama3'.
    # Why? 'nomic' is a specialized model just for turning text into numbers.
    # It is ~20x faster than Llama3 for this specific task and often more accurate for search.
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # =============================================================================
    # 4. MEMORY CHECK (Persistence)
    # Check if we have already read and saved this book before.
    # =============================================================================
    if os.path.exists(DB_PATH):
        print(f"Loading existing index from {DB_PATH}...")
        # LOAD: If the folder exists, load the "brain" instantly from disk.
        # This skips the slow PDF reading process completely.
        vector_db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        # CREATE: If no saved folder, we must process the PDF from scratch.
        print("Index not found. Creating new one with fast embeddings...")
        
        # A. LOAD: Read the raw text from the PDF file
        print("Loading PDF...")
        docs = PyPDFLoader(PDF_PATH).load()

        # B. SPLIT: Cut the book into smaller "chunks" (paragraphs)
        # chunk_size=900: roughly 900 characters per chunk
        # chunk_overlap=150: keep some context from previous chunk so sentences aren't cut in half
        print("Splitting into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
        chunks = splitter.split_documents(docs)

        # C. EMBED & INDEX: Convert chunks into numbers (vectors) and store them
        print("Creating embeddings + FAISS index (using nomic-embed-text)...")
        vector_db = FAISS.from_documents(chunks, embeddings)
        
        # D. SAVE: Save this processed data to the hard drive so we never have to do step A-C again
        vector_db.save_local(DB_PATH)
        print(f"Index saved to {DB_PATH}")

    # =============================================================================
    # 5. RETRIEVAL SETUP
    # Configure how we want to search the database
    # =============================================================================
    # "k=10" means "Find the top 10 most relevant chunks for every question"
    retriever = vector_db.as_retriever(search_kwargs={"k": 10})
    
    # =============================================================================
    # 6. LLM SETUP (The "Brain")
    # =============================================================================
    # We use 'llama3' for the answering part because it is smart and articulate.
    # Note: We use 'nomic' for searching, but 'llama3' for talking.
    llm = ChatOllama(model="llama3")

    # =============================================================================
    # 7. INTERACTIVE LOOP
    # Keep asking the user for questions until they quit
    # =============================================================================
    while True:
        q = input("\nAsk (or 'quit'): ").strip()
        if q.lower() == "quit":
            break

        # Step 7a: RETRIEVE with SCORES
        # Use similarity_search_with_score to get the distance (lower is better for L2)
        # Returns a list of tuples: (Document, score)
        docs_and_scores = vector_db.similarity_search_with_score(q, k=10)
        
        # EXPLICITLY SORT by Score (Ascending: Lower distance = Better match)
        # This ensures #1 is always the mathematically "best" result.
        docs_and_scores.sort(key=lambda x: x[1])

        # Unpack just the documents for the context
        source_docs = [doc for doc, score in docs_and_scores]

        # Step 7b: CONTEXT BUILD
        # Format the found chunks into a single string to feed to the AI
        context = "\n\n".join(
            f"[p.{d.metadata.get('page', 0)+1}] {d.page_content}"
            for d in source_docs
        )

        # Step 7c: PROMPT ENGINEERING
        # Give the AI strict instructions on how to behave
        prompt = f"""
You are a helpful expert assistant. Your task is to answer the user's question clearly and comprehensively using ONLY the provided context.
Explain the concepts nicely in your own words to help the user understand, but ensure every fact comes from the context.
Important: When you state a fact, try to reference the page number if available (e.g. "On page 27, it says...").
If the answer is not in the context, say you couldn't find it in the provided text.

Question: {q}

Context:
{context}
""".strip()

        print("\nThinking...")
        
        # Step 7d: GENERATE ANSWER
        # Send the prompt + context to Llama3 to get the human-readable answer
        answer = llm.invoke(prompt)
        print("\nAI:", answer.content if hasattr(answer, "content") else answer)

        # Step 7e: SHOW EVIDENCE
        # Print the exact text chunks we used, so the user can verify
        print("\nTop quotes/citations:\n")
        for i, (d, score) in enumerate(docs_and_scores, start=1):
            page = d.metadata.get("page", None)
            # CLEANUP: Just use the filename, not the full path
            src = "The Book" 
            text = d.page_content.strip().replace("\n", " ")
            # Truncate very long quotes for display (optional)
            excerpt = text[:600] + ("..." if len(text) > 600 else "")

            # Score explanation: with FAISS L2, Lower score = Closer match.
            # 0.0 would be an identical match.
            score_str = f"{score:.4f}"

            if page is not None:
                # Apply the Page Offset calculation here for correct printed numbers
                print(f"{i}) {src} — p. {int(page) + 1 + PAGE_OFFSET} (Score: {score_str})")
            else:
                print(f"{i}) {src} (Score: {score_str})")
            print(f'   “{excerpt}”\n')

if __name__ == "__main__":
    start_rag()
