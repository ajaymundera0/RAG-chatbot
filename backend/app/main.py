from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil

from backend.app.config import settings
from backend.app.vector_store import PineconeVectorStore
from backend.app.ingestion import load_document, chunk_text
from backend.app.chat import stream_answer

app = FastAPI(title="Chat With Your Documents - RAG API")

# Setup CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector store globally
vector_store = None

@app.on_event("startup")
def startup_event():
    global vector_store
    settings.validate()
    vector_store = PineconeVectorStore()

class ChatRequest(BaseModel):
    query: str
    top_k: int = 4

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    filename = os.path.basename(file.filename)

    try:
        # Extract pages directly from the in-memory file object
        pages = load_document(file.file, filename)
        chunks = chunk_text(pages, chunk_size=1000, overlap=100)

        if not chunks:
            raise HTTPException(status_code=400, detail="No text extracted from file")

        # Index chunks
        vector_store.add_chunks(chunks, source=filename)

        return {"message": f"Successfully processed and indexed {filename}", "chunks_created": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        # Retrieve context
        retrieved_chunks = vector_store.search(request.query, top_k=request.top_k)
        
        # Return streaming response
        return StreamingResponse(
            stream_answer(request.query, retrieved_chunks), 
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend static files last so API routes take precedence
os.makedirs("frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
