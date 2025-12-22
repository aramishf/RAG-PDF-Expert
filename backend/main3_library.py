import os
import glob
from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================
DATA_FOLDER = "data"
DB_PATH = "faiss_index_library"

# Configure Page Offsets for specific books here.
# Format: "Filename.pdf": Offset_Value
# If a book isn't listed, it defaults to 0.
BOOK_OFFSETS = {
    "Philosophy-of-Teachings-of-Islam.pdf": -40,
    "another_book.pdf": 0,
}

def get_page_offset(filename):
    """Returns the page offset for a given file, defaulting to 0."""
    return BOOK_OFFSETS.get(filename, 0)

def start_rag():
    print(f"Initializing Library RAG (Scanning '{DATA_FOLDER}' for PDFs)...")
    
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    if os.path.exists(DB_PATH):
        print(f"Loading existing library index from {DB_PATH}...")
        vector_db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        print("Index not found. Building new library index...")
        
        # 1. Find all PDFs
        pdf_files = glob.glob(os.path.join(DATA_FOLDER, "*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {DATA_FOLDER}/")
            return

        all_docs = []
        
        # 2. Load each PDF
        print(f"Found {len(pdf_files)} books: {[os.path.basename(f) for f in pdf_files]}")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Loading: {os.path.basename(pdf_file)}...")
            loader = PyPDFLoader(pdf_file)
            book_docs = loader.load()
            all_docs.extend(book_docs)

        print(f"Total pages loaded: {len(all_docs)}")

        # 3. Split
        print("Splitting into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
        chunks = splitter.split_documents(all_docs)
        print(f"Total chunks created: {len(chunks)}")

        # 4. Embed & Index
        print("Creating embeddings + FAISS index (using nomic-embed-text)...")
        vector_db = FAISS.from_documents(chunks, embeddings)
        
        # 5. Save
        vector_db.save_local(DB_PATH)
        print(f"Library index saved to {DB_PATH}")

    retriever = vector_db.as_retriever(search_kwargs={"k": 10})
    llm = ChatOllama(model="llama3")

    while True:
        q = input("\nAsk the Library (or 'quit'): ").strip()
        if q.lower() == "quit":
            break

        # Retrieve with scores
        docs_and_scores = vector_db.similarity_search_with_score(q, k=10)
        docs_and_scores.sort(key=lambda x: x[1])
        source_docs = [doc for doc, score in docs_and_scores]

        # Context Build
        context_parts = []
        for d in source_docs:
            src_file = os.path.basename(d.metadata.get("source", "Unknown"))
            pg = d.metadata.get("page", 0) + 1
            context_parts.append(f"[{src_file}, p.{pg}] {d.page_content}")
        
        context = "\n\n".join(context_parts)

        # Expert Prompt
        prompt = f"""
You are a helpful expert assistant answering questions based on a library of provided books.
I have provided you with context from multiple books. Your task is to find the answer in the context.

Rules:
1. Answer the user's question clearly.
2. Ensure every fact is based strictly on the provided context.
3. You MUST reference the specific Book Name and Page Number for your facts (e.g. "According to 'Jesus in India', page 45...").
4. If the answer is not in the context, simply say you couldn't find it in the provided books.

Question: {q}

Context:
{context}
""".strip()

        print("\nThinking...")
        answer = llm.invoke(prompt)
        print("\nAI:", answer.content if hasattr(answer, "content") else answer)

        # Citations
        print("\nTop quotes/citations:\n")
        for i, (d, score) in enumerate(docs_and_scores, start=1):
            full_path = d.metadata.get("source", "Unknown")
            filename = os.path.basename(full_path)
            page = d.metadata.get("page", None)
            text = d.page_content.strip().replace("\n", " ")
            excerpt = text[:600] + ("..." if len(text) > 600 else "")
            score_str = f"{score:.4f}"

            if page is not None:
                # Dynamic Offset Calculation
                offset = get_page_offset(filename)
                printed_page = int(page) + 1 + offset
                print(f"{i}) {filename} — p. {printed_page} (Score: {score_str})")
            else:
                print(f"{i}) {filename} (Score: {score_str})")
            print(f'   “{excerpt}”\n')

if __name__ == "__main__":
    start_rag()
