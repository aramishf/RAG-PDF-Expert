from langchain_community.document_loaders import PyPDFLoader

pdf_file = "data_uploaded/RRKT.pdf"
print(f"Testing {pdf_file}...")

try:
    loader = PyPDFLoader(pdf_file)
    docs = loader.load()
    print(f"Total pages: {len(docs)}")
    
    if docs:
        print(f"\nFirst page content (first 500 chars):")
        print(docs[0].page_content[:500])
        print(f"\nTotal text length on first page: {len(docs[0].page_content)} characters")
    else:
        print("No pages loaded!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
