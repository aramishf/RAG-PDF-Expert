from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

load_dotenv()

PDF_PATH = "data/Philosophy-of-Teachings-of-Islam.pdf"

def start_rag():
    print("Loading PDF...")
    docs = PyPDFLoader(PDF_PATH).load()

    print("Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    print("Creating embeddings + FAISS index...")
    embeddings = OllamaEmbeddings(model="llama3")
    vector_db = FAISS.from_documents(chunks, embeddings)

    retriever = vector_db.as_retriever(search_kwargs={"k": 10})
    llm = ChatOllama(model="llama3")

    while True:
        q = input("\nAsk (or 'quit'): ").strip()
        if q.lower() == "quit":
            break

        # 1) Retrieve top docs (quotes)
        source_docs = retriever.invoke(q)

        # 2) Build a context for the model (optional summary)
        context = "\n\n".join(
            f"[p.{d.metadata.get('page', 0)+1}] {d.page_content}"
            for d in source_docs[:10]
        )

        # 3) Ask the model to answer ONLY from context
        prompt = f"""
You are a quote finder. Use ONLY the provided context. 
If the answer is not in the context, say you couldn't find it.
Prefer quoting exact lines.

Question: {q}

Context:
{context}
""".strip()

        answer = llm.invoke(prompt)
        print("\nAI:", answer.content if hasattr(answer, "content") else answer)

        # 4) Print top quotes with citations
        print("\nTop quotes/citations:\n")
        for i, d in enumerate(source_docs[:10], start=1):
            page = d.metadata.get("page", None)
            src = d.metadata.get("source", "PDF")
            text = d.page_content.strip().replace("\n", " ")
            excerpt = text[:600] + ("..." if len(text) > 600 else "")

            if page is not None:
                print(f"{i}) {src} — p. {int(page) + 1}")
            else:
                print(f"{i}) {src}")
            print(f'   “{excerpt}”\n')

if __name__ == "__main__":
    start_rag()
