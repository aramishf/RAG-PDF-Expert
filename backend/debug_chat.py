from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import os

INDEX_FOLDER = "faiss_index"

def test_chat(question):
    print("Loading index...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_db = FAISS.load_local(INDEX_FOLDER, embeddings, allow_dangerous_deserialization=True)
    
    # Retrieve
    print(f"Retrieving for query: '{question}'")
    docs_and_scores = vector_db.similarity_search_with_score(question, k=40)
    source_docs = [doc for doc, score in docs_and_scores]
    
    context_parts = []
    for d in source_docs:
        src = d.metadata.get("source", "Unknown")
        pg = d.metadata.get("page", 0) + 1
        context_parts.append(f"[{src}, p.{pg}]:\n{d.page_content}")
    context = "\n\n".join(context_parts)
    print(f"Context length: {len(context)}")

    # Prompt
    prompt = f"""You are an expert research assistant.

QUERY: {question}

SOURCE MATERIAL:
{context}

INSTRUCTIONS:
Analyze the source material and provide a structured response following these 4 STEPS exactly.

STEP 1 - EVIDENCE EXTRACTION
- List textual evidence directly relevant to the query.
- Format: "Verbatim quote..." [Source, p.XX]
- Classify claims if possible (Historical, Theological, etc.)

STEP 2 - ANALYSIS
- Analyze the extracted evidence.
- Explain the key arguments or narratives presented in the text.
- Connect the evidence to logical conclusions.
- "The text presents a perspective that..."

STEP 3 - GAP IDENTIFICATION
- Identify what is missing from the provided text to fully answer the query.
- Identify any assumptions the text makes (e.g. reader knowledge).
- "The text does not explain..."

STEP 4 - SYNTHESIS
- Synthesize a comprehensive final answer based on the analysis.
- Connect the claims to the final conclusion.
- Ensure the tone is objective and analytical.

CRITICAL CITATION RULES:
- ALWAYS use [Source, p.XX] format immediately after quotes.
- NO "References" list at the end.
- ALL claims must be grounded in the text.

    """.strip()

    print("Invoking LLM (mistral)...")
    llm = ChatOllama(model="mistral")
    response = llm.invoke(prompt)
    print("Response received:")
    print(response.content)

if __name__ == "__main__":
    # Use the specific user query
    q = "What quranic evidences are provided on the death of Isa and not on the cross and not his bodily ascension?"
    test_chat(q)
