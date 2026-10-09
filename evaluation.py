import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from rag_pipeline import rag_pipeline
from config import settings
import re
import os

EVALUATION_CASES = [
    {
        "id": "Test 1",
        "question": "I have 72% attendance. How many attendance marks will I get?",
        "expected_outcome": "The student will receive 4 attendance marks, according to the attendance evaluation table."
    },
    {
        "id": "Test 2",
        "question": "I study at the Ratnam campus. I got sick and need medical leave. Who do I email and how many days do I have to submit my documents?",
        "expected_outcome": "Direct the student to Yashaswini Ma'am, the Ratnam campus manager, and explain that supporting medical leave documents must be submitted within 7 days, subject to the handbook's stated submission requirements."
    },
    {
        "id": "Test 3",
        "question": "We want to start a new Cybersecurity society under the Tech Club. Do we ask Management directly?",
        "expected_outcome": "A proposed new student organization requires support from at least 40% of the total batch students. The formal proposal and verifiable supporting signatures must first be submitted to the designated Faculty Coordinator for review. Students must not bypass the faculty and approach Management directly about club operations."
    },
    {
        "id": "Test 4",
        "question": "How much is the fine for smoking a cigarette on campus?",
        "expected_outcome": "Explain that tobacco is prohibited on campus and that violations may lead to disciplinary action under the Code of Conduct Policy. Explicitly state that the handbook does not specify a monetary fine."
    }
]

def run_evaluations():
    print("Starting evaluations...")
    if not settings.google_api_key:
        print("Google API Key not set. Cannot run actual evaluations. Generating mock evaluation results...")
        mock_results = []
        for test in EVALUATION_CASES:
            mock_results.append({
                "Test ID": test["id"],
                "Question": test["question"],
                "Retrieved Context": "Mock context from handbook (requires API key to actually retrieve).",
                "Expected Outcome": test["expected_outcome"],
                "Actual Answer": "Mock answer (requires API key to generate).",
                "Judge Score (1-5)": 0,
                "Evaluation Reasoning": "Evaluation skipped due to missing Google API Key."
            })
        df = pd.DataFrame(mock_results)
        df.to_csv("rag_eval_scores.csv", index=False)
        print("Evaluations complete. Results saved to rag_eval_scores.csv.")
        return

    if not rag_pipeline.vector_store:
        print("Vector store not initialized. Please ingest the document first.")
        return

    judge_llm = ChatGoogleGenerativeAI(model=settings.generation_model, temperature=0.0, google_api_key=settings.google_api_key)

    eval_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert AI evaluator. You are grading the answer of a Student Policy Advisor RAG system.
Evaluate the 'Actual Answer' against the 'Expected Outcome' for the given 'Question'.
The system has strict anti-hallucination guardrails and must cite the handbook accurately.
Rate the answer on a scale of 1 to 5 based on source fidelity, correctness, completeness, and compliance with the no-hallucination constraint.
Also provide your reasoning.
Return your response exactly in this format:
Score: <1-5>
Reasoning: <your reasoning>"""),
        ("human", "Question: {question}\nExpected Outcome: {expected_outcome}\nActual Answer: {actual_answer}")
    ])

    judge_chain = eval_prompt | judge_llm | StrOutputParser()

    results = []

    for test in EVALUATION_CASES:
        print(f"Running {test['id']}...")
        question = test["question"]
        expected = test["expected_outcome"]

        try:
            actual_answer, sources_data = rag_pipeline.chat(question)
            context = "\n".join([s["content"] for s in sources_data])
        except Exception as e:
            actual_answer = f"Error: {e}"
            context = ""
        
        judge_input = {
            "question": question,
            "expected_outcome": expected,
            "actual_answer": actual_answer
        }
        
        evaluation = judge_chain.invoke(judge_input)
        
        # Parse score and reasoning
        score_match = re.search(r"Score:\s*(\d+)", evaluation)
        score = int(score_match.group(1)) if score_match else None
        
        reasoning_match = re.search(r"Reasoning:\s*(.*)", evaluation, re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else evaluation

        results.append({
            "Test ID": test["id"],
            "Question": question,
            "Retrieved Context": context,
            "Expected Outcome": expected,
            "Actual Answer": actual_answer,
            "Judge Score (1-5)": score,
            "Evaluation Reasoning": reasoning
        })

    df = pd.DataFrame(results)
    df.to_csv("rag_eval_scores.csv", index=False)
    print("Evaluations complete. Results saved to rag_eval_scores.csv.")

if __name__ == "__main__":
    run_evaluations()
