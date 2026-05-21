import streamlit as st
import os
import tempfile
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

# =============================================================================
# CONFIG & STATE
# =============================================================================
st.set_page_config(page_title="Local RAG Scholar", page_icon="🎓", layout="wide")

if "vector_db" not in st.session_state:
    st.session_state["vector_db"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# =============================================================================
# BACKEND LOGIC
# =============================================================================
def process_uploaded_files(uploaded_files):
    """
    Reads uploaded PDF files, creates chunks, and builds a FAISS index.
    Returns: vector_db
    """
    all_docs = []
    
    with st.status("Processing Documents... ⏳", expanded=True) as status:
        for uploaded_file in uploaded_files:
            st.write(f"Reading: **{uploaded_file.name}**...")
            
            # Save to temporary file because PyPDFLoader needs a path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                # Add source metadata explicitly
                for doc in docs:
                    doc.metadata["source"] = uploaded_file.name
                all_docs.extend(docs)
            finally:
                os.remove(tmp_path) # Clean up temp file

        st.write("Splitting text into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
        chunks = splitter.split_documents(all_docs)

        st.write(f"Creating Embeddings (nomic-embed-text) for {len(chunks)} chunks...")
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory="./chroma_db_streamlit"
        )
        status.update(label="Index Created Successfully! ✅", state="complete", expanded=False)
        
    return vector_db

def get_answer(question):
    """
    Retrieves context and generates an answer using Llama3.
    """
    vector_db = st.session_state["vector_db"]
    llm = ChatOllama(model="llama3")

    # 1. Retrieve
    docs_and_scores = vector_db.similarity_search_with_score(question, k=10)
    # Sort by Score (Lower is better for L2 distance)
    docs_and_scores.sort(key=lambda x: x[1])
    
    source_docs = [doc for doc, score in docs_and_scores]

    # 2. Build Context
    context_parts = []
    for d in source_docs:
        src = d.metadata.get("source", "Unknown")
        pg = d.metadata.get("page", 0) + 1
        context_parts.append(f"[{src}, p.{pg}] {d.page_content}")
    
    context = "\n\n".join(context_parts)

    # 3. Prompt
    prompt = f"""
You are a helpful expert assistant answering questions based on a library of provided books.
I have provided you with context from multiple books. Your task is to find the answer in the context.

Rules:
1. Answer the user's question clearly.
2. Ensure every fact is based strictly on the provided context.
3. You MUST reference the specific Book Name and Page Number for your facts (e.g. "According to 'Jesus in India', page 45...").
4. If the answer is not in the context, simply say you couldn't find it in the provided books.

Question: {question}

Context:
{context}
"""

    # 4. Generate
    response = llm.invoke(prompt)
    answer_text = response.content

    return answer_text, docs_and_scores

# =============================================================================
# FRONTEND UI
# =============================================================================
st.title("🎓 Local RAG Scholar")
st.markdown("##### Private, Offline Document Assistant powered by Ollama")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Document Library")
    uploaded_files = st.file_uploader(
        "Upload PDF Books", 
        type=["pdf"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("Process Documents", type="primary"):
            st.session_state["vector_db"] = process_uploaded_files(uploaded_files)
            st.toast("Knowledge Base Updated!", icon="🧠")
    
    st.markdown("---")
    st.caption("Settings")
    st.caption("Model: `llama3`")
    st.caption("Embeddings: `nomic-embed-text`")

# --- CHAT INTERFACE ---

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "citations" in msg:
            with st.expander(f"📚 View {len(msg['citations'])} Citations & Scores"):
                for i, (doc, score) in enumerate(msg["citations"], 1):
                    src = doc.metadata.get("source", "Unknown")
                    pg = doc.metadata.get("page", 0) + 1
                    st.markdown(f"**{i}. {src}** (p.{pg}) - *Score: {score:.4f}*")
                    st.caption(doc.page_content[:300] + "...")

# Chat Input
if question := st.chat_input("Ask a question about your books..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    # Generate Response
    if st.session_state["vector_db"] is None:
        st.error("Please upload and process documents first!")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer_text, citations = get_answer(question)
                st.write(answer_text)
                
                # Show Citations in Expander
                with st.expander(f"📚 View {len(citations)} Citations & Scores"):
                    for i, (doc, score) in enumerate(citations, 1):
                        src = doc.metadata.get("source", "Unknown")
                        pg = doc.metadata.get("page", 0) + 1
                        st.markdown(f"**{i}. {src}** (p.{pg}) - *Score: {score:.4f}*")
                        st.caption(doc.page_content[:300] + "...")

        # Add Assistant Message to History
        st.session_state.messages.append({
            "role": "assistant", 
            "content": answer_text,
            "citations": citations
        })
