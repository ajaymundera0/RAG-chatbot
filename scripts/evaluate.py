import json
import os
import sys

# Ensure the root directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from backend.app.config import settings
from backend.app.vector_store import PineconeVectorStore
from backend.app.ingestion import load_document, chunk_text
from backend.app.chat import generate_answer

# --- Retrieval settings under test. Change these, re-run, compare scores. ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
TOP_K = 4

# Fixed corpus the eval questions are written against.
EVAL_DOCS = [
    "data/Home_Coffee_Brewing_Guide.pdf",
    "data/Fasttracking the course of AI.pdf"
]


def build_index() -> PineconeVectorStore:
    """
    Rebuilds a dedicated eval index from a fixed document list.

    Uses its own collection so it never clobbers documents uploaded through the app,
    and re-ingests on every run so a score depends only on the settings above.
    """
    store = PineconeVectorStore(collection_name="eval")
    for path in EVAL_DOCS:
        with open(path, "rb") as f:
            pages = load_document(f, os.path.basename(path))
        chunks = chunk_text(pages, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        store.add_chunks(chunks, source=os.path.basename(path))
        print(f"  Indexed {os.path.basename(path)}: {len(pages)} pages -> {len(chunks)} chunks")
    return store

def grade_answer(client: OpenAI, question: str, expected: str, actual: str) -> bool:
    """
    Uses the LLM as a judge to determine if the actual answer matches the expected answer semantically.
    """
    system_prompt = (
        "You are an impartial grader evaluating an AI's response to a user's question.\n"
        "You will be given the Question, the Expected Answer, and the Actual Answer.\n"
        "Your job is to determine if the Actual Answer is correct based on the Expected Answer.\n"
        "The Actual Answer does not need to use the exact same words, but it must contain the same factual information.\n"
        "If the Expected Answer is 'I don't know based on these documents.', the Actual Answer must also express an inability to answer based on the context.\n"
        "Respond with EXACTLY '1' if the answer is correct, and '0' if it is incorrect. Do NOT write any explanations, do NOT think out loud, and do NOT include any other text whatsoever. Output a single character."
    )
    
    user_prompt = f"Question: {question}\nExpected Answer: {expected}\nActual Answer: {actual}"
    
    response = client.chat.completions.create(
        model=settings.JUDGE_MODEL,  # pinned, so tuning CHAT_MODEL doesn't move the grader too
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0, # Strict and deterministic
        # A reasoning judge spends this budget on hidden reasoning tokens before it
        # emits the verdict. Too low and it truncates mid-thought, returning empty
        # content that silently scores as a FAIL. Keep the ceiling generous.
        max_tokens=2048
    )

    choice = response.choices[0]
    grade_str = (choice.message.content or "").strip()
    if not grade_str:
        raise RuntimeError(
            f"Judge returned no verdict (finish_reason={choice.finish_reason}). "
            "If it is 'length', raise max_tokens."
        )
    # startswith, not ==, so a judge that adds a trailing word doesn't silently fail the case
    return grade_str.startswith("1")

def run_evaluation():
    print("Starting Evaluation Harness...")
    
    # Load dataset
    dataset_path = os.path.join("data", "eval_set.json")
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found.")
        return
        
    with open(dataset_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
        
    print(f"Loaded {len(eval_data)} test cases.\n")
    
    # Rebuild the index so this run is reproducible
    print("Building eval index...")
    vector_store = build_index()
    print()
    client = OpenAI(base_url=settings.CHAT_BASE_URL, api_key=settings.CHAT_API_KEY)
    
    passed = 0
    total = len(eval_data)
    
    for idx, test_case in enumerate(eval_data, 1):
        question = test_case["question"]
        expected = test_case["expected_answer"]
        
        print(f"Test {idx}/{total}")
        print(f"Q: {question}")
        
        # 1. Retrieve context
        chunks = vector_store.search(question, top_k=TOP_K)
        
        # 2. Generate answer
        actual_answer = generate_answer(question, chunks)
        print(f"Expected: {expected}")
        print(f"Actual:   {actual_answer}")

        # 3. Grade
        is_correct = grade_answer(client, question, expected, actual_answer)
        if is_correct:
            print("[PASS]\n")
            passed += 1
        else:
            print("[FAIL]\n")
            
    # Calculate summary score
    score_percentage = (passed / total) * 100
    print("-" * 30)
    print("EVALUATION SUMMARY")
    print("-" * 30)
    print(f"Chat model  : {settings.CHAT_MODEL}")
    print(f"Judge model : {settings.JUDGE_MODEL}")
    print(f"Retrieval   : chunk={CHUNK_SIZE} overlap={CHUNK_OVERLAP} top_k={TOP_K}")
    print(f"Total Tests : {total}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {total - passed}")
    print(f"Score       : {score_percentage:.1f}%")
    
if __name__ == "__main__":
    run_evaluation()
