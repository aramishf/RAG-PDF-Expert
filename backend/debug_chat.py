from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import os

INDEX_FOLDER = "faiss_index"

def test_chat():
    print("Loading index...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_db = FAISS.load_local(INDEX_FOLDER, embeddings, allow_dangerous_deserialization=True)
    
    question = "Is Jesus death mentioned in the text?"
    print(f"Question: {question}")
    
    # Retrieve
    docs_and_scores = vector_db.similarity_search_with_score(question, k=5)
    source_docs = [doc for doc, score in docs_and_scores]
    
    context_parts = []
    for d in source_docs:
        src = d.metadata.get("source", "Unknown")
        pg = d.metadata.get("page", 0) + 1
        context_parts.append(f"[{src}, p.{pg}] {d.page_content}")
    context = "\n\n".join(context_parts)
    print(f"Context length: {len(context)}")

    # Prompt
    prompt = f"""
You are an expert research assistant.
Question: {question}
Context:
{context}
    """.strip()

    print("Invoking LLM...")
    llm = ChatOllama(model="llama3")
    response = llm.invoke(prompt)
    print("Response received:")
    print(response.content)

if __name__ == "__main__":
    test_chat()
