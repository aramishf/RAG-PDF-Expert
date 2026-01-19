from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import os

INDEX_FOLDER = "faiss_index"

def test_faiss():
    if not os.path.exists(INDEX_FOLDER):
        print("Index folder not found!")
        return

    print("Loading index...")
    try:
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vector_db = FAISS.load_local(INDEX_FOLDER, embeddings, allow_dangerous_deserialization=True)
        print("Index loaded.")
        
        print("Testing search...")
        results = vector_db.similarity_search_with_score("God", k=1)
        print(f"Docs found: {len(results)}")
        print(results[0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_faiss()
