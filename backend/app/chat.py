from openai import OpenAI
from backend.app.config import settings

def generate_answer(query: str, retrieved_chunks: list[dict]) -> str:
    """
    Constructs a prompt using retrieved chunks and calls the LLM.
    Strictly instructs the model to only use the provided context.
    """
    client = OpenAI(base_url=settings.HF_BASE_URL, api_key=settings.HF_TOKEN)
    
    # Format the context from retrieved chunks
    context_text = ""
    for idx, chunk in enumerate(retrieved_chunks, 1):
        context_text += f"\n--- Source {idx} ---\n{chunk['text']}\n"
    
    system_prompt = (
        "You are a helpful assistant. You will be provided with a user's question and several context chunks from uploaded documents.\n"
        "Your task is to answer the user's question using ONLY the provided context.\n"
        "If the context does not contain the information needed to answer the question, you must respond exactly with: "
        "'I don't know based on these documents.'\n"
        "Do not include any outside knowledge or information."
    )
    
    user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}"
    
    response = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0 # Low temperature for more factual responses
    )
    
    return response.choices[0].message.content.strip()


def stream_answer(query: str, retrieved_chunks: list[dict]):
    """
    Constructs a prompt using retrieved chunks and calls the LLM with streaming.
    Yields string tokens one by one.
    """
    client = OpenAI(base_url=settings.HF_BASE_URL, api_key=settings.HF_TOKEN)
    
    context_text = ""
    for idx, chunk in enumerate(retrieved_chunks, 1):
        context_text += f"\n--- Source {idx} ---\n{chunk['text']}\n"
    
    system_prompt = (
        "You are a helpful assistant. You will be provided with a user's question and several context chunks from uploaded documents.\n"
        "Your task is to answer the user's question using ONLY the provided context.\n"
        "If the context does not contain the information needed to answer the question, you must respond exactly with: "
        "'I don't know based on these documents.'\n"
        "Do not include any outside knowledge or information."
    )
    
    user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}"
    
    response_stream = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        stream=True
    )
    
    for chunk in response_stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
