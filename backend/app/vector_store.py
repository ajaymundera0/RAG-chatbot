import os
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from backend.app.config import settings
import uuid

class PineconeVectorStore:
    def __init__(self, collection_name: str = "rag-chatbot"):
        # Initialize Pinecone and OpenAI clients
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.EMBEDDING_MODEL
        
        # We use the config name or fallback to the provided name
        self.index_name = settings.PINECONE_INDEX_NAME or collection_name

        # Ensure index exists
        if self.index_name not in [index.name for index in self.pc.list_indexes()]:
            # text-embedding-3-small outputs 1536 dimensions
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
        self.index = self.pc.Index(self.index_name)

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Fetch embeddings from OpenAI"""
        if not texts:
            return []
        response = self.openai_client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        return [data.embedding for data in response.data]

    def add_chunks(self, chunks: list[dict], source: str):
        """Adds structured chunks to the vector store, preserving metadata."""
        if not chunks:
            return

        # Optional: delete old chunks for this source if replacing
        # Wait, Pinecone Serverless doesn't support delete by metadata yet in some tiers,
        # but we can do it if we track IDs, or just ignore and append for this demo.
        # Let's generate consistent IDs based on source + chunk index so they overwrite.
        
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self._get_embeddings(texts)
        
        vectors = []
        for i, chunk_data in enumerate(chunks):
            chunk_id = f"{source}_chunk_{i}"
            meta = dict(chunk_data.get("metadata", {}))
            meta["source"] = source
            meta["chunk_index"] = i
            meta["text"] = chunk_data["text"]  # Store text in metadata to retrieve it
            
            vectors.append({
                "id": chunk_id,
                "values": embeddings[i],
                "metadata": meta
            })
            
        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            self.index.upsert(vectors=vectors[i:i + batch_size])

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        """Searches for the most similar chunks to the query."""
        query_embedding = self._get_embeddings([query])[0]
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        if not results.matches:
            return []
            
        retrieved = []
        for match in results.matches:
            meta = match.metadata
            text = meta.pop("text", "")
            retrieved.append({
                "text": text,
                "metadata": meta,
                "distance": match.score # Pinecone returns similarity score
            })
        return retrieved

