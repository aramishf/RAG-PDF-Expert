
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
import os

INDEX_FOLDER = "faiss_index"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def debug_retrieval(query, k=35):
    if not os.path.exists(INDEX_FOLDER):
        print("No index found.")
        return

    print(f"Loading index from {INDEX_FOLDER}...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
    vector_db = FAISS.load_local(INDEX_FOLDER, embeddings, allow_dangerous_deserialization=True)
    
    print(f"Searching for: '{query}' with k={k}")
    docs_and_scores = vector_db.similarity_search_with_score(query, k=k)
    
    print(f"\nFound {len(docs_and_scores)} documents:\n")
    for i, (doc, score) in enumerate(docs_and_scores, 1):
        source = doc.metadata.get('source', 'Unknown')
        page = doc.metadata.get('page', 'Unknown')
        print(f"--- Doc {i} (Score: {score:.4f}) ---")
        print(f"Source: {source}, Page: {page}")
        print(f"Content Preview: {doc.page_content[:200]}...")
        print("-" * 50)

if __name__ == "__main__":
    debug_retrieval("What quranic evidences are provided on the death of Isa and not on the cross and not his bodily ascension?")
