import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from sentence_transformers import SentenceTransformer
from backend.app.config import settings

class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str):
        # We strip the huggingface prefix to load locally via sentence-transformers
        clean_name = model_name.replace("sentence-transformers/", "")
        self._model = SentenceTransformer(clean_name)

    def __call__(self, input: Documents) -> Embeddings:
        # SentenceTransformer.encode returns a numpy array or tensor, we convert to list
        embeddings = self._model.encode(input)
        return embeddings.tolist()

class ChromaVectorStore:
    def __init__(self, collection_name: str = "documents"):
        # Use a persistent client for Phase 2 so data survives FastAPI reloads
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_fn = SentenceTransformerEmbeddingFunction(settings.EMBEDDING_MODEL)
        
        # Create a fresh collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_chunks(self, chunks: list[str], source: str):
        """Adds text chunks to the vector store with metadata."""
        if not chunks:
            return

        ids = [f"{source}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        """Searches for the most similar chunks to the query."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Chroma returns lists of lists because we queried with a list of 1 query.
        # We'll flatten it to a list of dicts for our use case.
        if not results["documents"] or not results["documents"][0]:
            return []
            
        retrieved = []
        for i in range(len(results["documents"][0])):
            retrieved.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results["distances"] else None
            })
        return retrieved
