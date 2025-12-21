# RAG System: Development & Optimization Summary

## Project Overview
Developed a **Retrieval-Augmented Generation (RAG)** system capable of ingesting, indexing, and semantically querying complex PDF documents (e.g., *The Philosophy of the Teachings of Islam*). The system allows users to ask natural language questions and receive accurate, context-aware answers grounded in the source text, complete with direct page-level citations.

## Technical Architecture & Stack
-   **Language**: Python 3.14
-   **LLM Orchestration**: LangChain (Community & Ollama integrations)
-   **Local Inference**: Ollama (Self-hosted LLM api)
-   **Models**:
    -   **Inference**: `llama3` (8B parameters) for high-quality natural language synthesis.
    -   **Embedding**: `nomic-embed-text` for high-performance semantic vectorization.
-   **Vector Database**: FAISS (Facebook AI Similarity Search) for efficient reading and similarity search.
-   **Document Processing**: `pypdf` for extraction, `RecursiveCharacterTextSplitter` for context-aware chunking.

## Key Features & Optimizations (Resume Highlights)

### 1. Zero-Cost Local Ingestion Pipeline
-   Migrated from OpenAI API to a fully local stack using **Ollama**, eliminating API costs and ensuring data privacy.
-   Engineered a seamless switch between models, utilizing `nomic-embed-text` for embeddings (20x faster than generic LLMs) while retaining `llama3` for reasoning.

### 2. High-Performance Persistence (Caching)
-   Identified a critical bottleneck in startup time (PDF re-processing on every run).
-   Implemented **Vector Store Persistence**: The system now serializes the FAISS index to disk (`faiss_index_fast`).
-   **Result**: Reduced initialization time from **~3 minutes to <1 second** for subsequent runs, allowing for instant query capability.

### 3. Precision Citation System with Offset Logic
-   Developed a custom "Quote Finding" implementation that retrieves the top 10 most relevant source chunks.
-   Solved a common real-world data discrepancy where PDF page indices did not match printed page numbers.
-   Implemented a configurable `PAGE_OFFSET` logic to mathematically correct citations, ensuring the AI output references the physical book pages accurately (e.g., mapping PDF page 50 to Printed Page 10).

### 4. Code Evolution & Refactoring
-   **`main.py`**: Initial rigid "Quote Finder" prototype.
-   **`main1.py`**: "Helpful Expert" version with improved prompt engineering for conversational yet grounded answers.
-   **`main2.py`**: Production-optimized version featuring:
    -   Persistence/Caching check.
    -   Specialized embedding models.
    -   Full code documentation/commenting for maintainability.

## Generalizability
While currently configured for a specific book, this architecture is **content-agnostic**. It can be deployed to process any technical manual, legal document, or textbook simply by changing the `PDF_PATH` config, making it a highly versatile enterprise search tool.
