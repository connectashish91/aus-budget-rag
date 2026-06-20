import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_vectorstore, build_qa_chain
from positive import POSITIVE_GOLDENS
from negative import NEGATIVE_GOLDENS
from edge import EDGE_GOLDENS
from hallucination import HALLUCINATION_GOLDENS
from adversarial import ADVERSARIAL_GOLDENS
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, GEval
from deepeval.models import AnthropicModel
from deepeval import evaluate

# ── Setup pipeline ──────────────────────────────────────────
vectorstore = create_vectorstore()
chain, retriever = build_qa_chain(vectorstore)

def ask_budget_rag(question):
    answer = chain.invoke(question)
    sources = retriever.invoke(question)
    contexts = [doc.page_content for doc in sources]
    return {"answer": answer, "contexts": contexts}

# ── Build test cases per category (kept separate) ──────────
def build_test_cases(goldens):
    test_cases = []
    for golden in goldens:
        result = ask_budget_rag(golden.input)
        test_cases.append(
            LLMTestCase(
                input=golden.input,
                actual_output=result["answer"],
                expected_output=golden.expected_output,
                retrieval_context=result["contexts"]
            )
        )
    return test_cases

print("Building test cases — this calls the live RAG pipeline for every question...")
positive_cases = build_test_cases(POSITIVE_GOLDENS)
negative_cases = build_test_cases(NEGATIVE_GOLDENS)
edge_cases = build_test_cases(EDGE_GOLDENS)
hallucination_cases = build_test_cases(HALLUCINATION_GOLDENS)
adversarial_cases = build_test_cases(ADVERSARIAL_GOLDENS)

# ── Define metrics ───────────────────────────────────────────
judge_model = AnthropicModel(model="claude-haiku-4-5-20251001")

faithfulness_metric = FaithfulnessMetric(threshold=0.7, model=judge_model, include_reason=True)
relevancy_metric = AnswerRelevancyMetric(threshold=0.7, model=judge_model, include_reason=True)

refusal_correctness_metric = GEval(
    name="Correct Refusal Behaviour",
    criteria="""Determine whether the actual output correctly refuses or 
    declines to answer when the question is adversarial, out-of-scope, or 
    asks for fabricated information. The actual output should match the 
    spirit of the expected output, which describes that no such information 
    exists in the Australian Budget documents. The actual output does not 
    need to match the expected output word-for-word — it needs to demonstrate 
    the same refusal behaviour and avoid hallucinating an answer.""",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.EXPECTED_OUTPUT
    ],
    model=judge_model,
    threshold=0.7
)

# ── Run evaluation per category ──────────────────────────────
print("\n" + "="*60)
print("POSITIVE TEST CASES")
print("="*60)
evaluate(positive_cases, [faithfulness_metric, relevancy_metric])

print("\n" + "="*60)
print("NEGATIVE TEST CASES")
print("="*60)
evaluate(negative_cases, [refusal_correctness_metric])

print("\n" + "="*60)
print("EDGE TEST CASES")
print("="*60)
evaluate(edge_cases, [faithfulness_metric, relevancy_metric])

print("\n" + "="*60)
print("HALLUCINATION TEST CASES")
print("="*60)
evaluate(hallucination_cases, [refusal_correctness_metric])

print("\n" + "="*60)
print("ADVERSARIAL TEST CASES")
print("="*60)
evaluate(adversarial_cases, [refusal_correctness_metric])