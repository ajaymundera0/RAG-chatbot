import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.config import settings
from backend.app.vector_store import PineconeVectorStore
from backend.app.ingestion import load_document, chunk_text
from backend.app.chat import generate_answer

def main():
    settings.validate()
    
    print("Initializing vector store (this might take a second to load the embedding model)...")
    vector_store = PineconeVectorStore()
    
    sample_file = os.path.join(os.path.dirname(__file__), "..", "data", "sample.txt")
    print(f"Loading document: {sample_file}")
    
    with open(sample_file, "rb") as f:
        text = load_document(f, "sample.txt")
    chunks = chunk_text(text, chunk_size=2000, overlap=500) # Smaller chunks for our tiny text
    
    print(f"Created {len(chunks)} chunks. Indexing...")
    vector_store.add_chunks(chunks, source="sample.txt")
    print("Indexing complete!\n")
    
    print("=== Terminal RAG (Type 'exit' or 'quit' to stop) ===")
    
    while True:
        try:
            query = input("\nQ: ")
            if query.strip().lower() in ["exit", "quit"]:
                break
            if not query.strip():
                continue
                
            print("Retrieving context...")
            retrieved = vector_store.search(query, top_k=2)
            
            print("Generating answer...")
            answer = generate_answer(query, retrieved)
            
            print(f"\nA: {answer}\n")
            
        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
