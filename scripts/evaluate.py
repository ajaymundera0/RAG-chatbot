import json
import os
import sys

# Ensure the root directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from backend.app.config import settings
from backend.app.vector_store import ChromaVectorStore
from backend.app.chat import generate_answer

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
        model=settings.CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0, # Strict and deterministic
        max_tokens=100
    )
    
    content = response.choices[0].message.content
    grade_str = (content or "").strip()
    if "1" not in grade_str and "0" not in grade_str:
        print(f"  [Grader Output]: {grade_str!r}")
    return "1" in grade_str

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
    
    # Initialize components
    vector_store = ChromaVectorStore()
    client = OpenAI(base_url=settings.OPENROUTER_BASE_URL, api_key=settings.OPENROUTER_API_KEY)
    
    passed = 0
    total = len(eval_data)
    
    for idx, test_case in enumerate(eval_data, 1):
        question = test_case["question"]
        expected = test_case["expected_answer"]
        
        print(f"Test {idx}/{total}")
        print(f"Q: {question}")
        
        # 1. Retrieve context
        chunks = vector_store.search(question, top_k=4)
        
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
    print(f"Total Tests : {total}")
    print(f"Passed      : {passed}")
    print(f"Failed      : {total - passed}")
    print(f"Score       : {score_percentage:.1f}%")
    
if __name__ == "__main__":
    run_evaluation()
