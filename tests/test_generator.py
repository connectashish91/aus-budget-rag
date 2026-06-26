import os
import sys
from dotenv import load_dotenv
from typing import TypedDict
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from positive import POSITIVE_GOLDENS
from negative import NEGATIVE_GOLDENS
from edge import EDGE_GOLDENS
from hallucination import HALLUCINATION_GOLDENS
from adversarial import ADVERSARIAL_GOLDENS

sys.path.insert(0, "tests")  # adjust if your golden files live elsewhere
load_dotenv()




# ── State ─────────────────────────────────────────────────
class AgentState(TypedDict):
    requirement: str
    test_cases: str
    review_feedback: str
    final_test_cases: str
    refined: bool
    existing_tests: str
    refine_count: int

# ── LLM ───────────────────────────────────────────────────
llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=4096
)

# ── Node 1: Generate ───────────────────────────────────────
def generate_node(state: AgentState) -> AgentState:
    print(f"\n[Agent] Generating test cases...")
    prompt = f"""You are a senior QA engineer. Generate test cases in Gherkin format 
for the following requirement. Cover happy path, edge cases, and negative cases.

All monetary amounts in your test cases must use Australian dollars, formatted 
as "$X,XXX,XXX.XX AUD" — never use £, €, or unspecified currency symbols.

Requirement: {state['requirement']}

Format:
Scenario: [name]
  Given [precondition]
  When [action]
  Then [expected result]
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "test_cases": response.content}

# ── Node 2: Review ───────────────────────────────────────
def review_node(state: AgentState) -> AgentState:
    print("[Agent] Reviewing for coverage gaps...")
    prompt = f"""You are a QA lead reviewing test coverage.

Requirement: {state['requirement']}

Newly generated test cases:
{state['test_cases']}

Test cases that ALREADY EXIST in our real test suite (do not repeat these):
{state['existing_tests']}

Identify gaps that are NOT already covered by either the newly generated 
test cases or the existing suite. If everything meaningful is already 
covered, say so clearly rather than inventing redundant scenarios.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "review_feedback": response.content}

def should_refine(state: AgentState) -> str:
    feedback_lower = state["review_feedback"].lower()
    gap_signals = ["missing", "gap", "should also", "doesn't cover", "lacks"]
    if any(signal in feedback_lower for signal in gap_signals) and state["refine_count"] < 2:
        return "refine"
    return "done"

def refine_node(state: AgentState) -> AgentState:
    print(f"[Agent] Refining (refine pass {state['refine_count'] + 1})...")
    prompt = f"""Improve these test cases based on the reviewer feedback below.
Keep Gherkin format. Add any missing scenarios identified.

Original test cases: {state['test_cases']}
Reviewer feedback: {state['review_feedback']}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {
        **state, 
        "test_cases": response.content,  # feed refined version back in as the new test_cases
        "final_test_cases": response.content,
        "refined": True,
        "refine_count": state["refine_count"] + 1
    }


def summarize_existing_tests():
    all_goldens = (
        POSITIVE_GOLDENS + NEGATIVE_GOLDENS + EDGE_GOLDENS 
        + HALLUCINATION_GOLDENS + ADVERSARIAL_GOLDENS
    )
    lines = [f"- {g.input}" for g in all_goldens]
    return "\n".join(lines)


# ── Build graph ───────────────────────────────────────────
def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("generate", generate_node)
    workflow.add_node("review", review_node)
    workflow.add_node("refine", refine_node)
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", "review")
    workflow.add_conditional_edges("review", should_refine, {"refine": "refine", "done": END})
    workflow.add_edge("refine", "review")  
    return workflow.compile()

# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    agent = build_agent()
    existing = summarize_existing_tests()

    requirement = """
    The Australian Budget RAG system must answer user questions about the 
    2026-27 Federal Budget using only information retrieved from the official 
    budget documents. 

    The system must:
    - Provide accurate, grounded answers when the relevant information exists 
      in the retrieved context, including correct figures, dates, and policy details
    - Clearly state that information could not be found when a question falls 
      outside the scope of the budget documents (e.g. unrelated topics, other 
      financial years, or general knowledge questions)
    - Resist attempts to override its grounding behaviour through instructions 
      embedded within the user's question itself (e.g. "answer even if the 
      information is missing", "ignore previous instructions")
    - Avoid stating incorrect dates, figures, or details even when the correct 
      policy or topic is identified
    """

    result = agent.invoke({
        "requirement": requirement,
        "existing_tests": existing,
        "test_cases": "",
        "review_feedback": "",
        "final_test_cases": "",
        "refine_count": 0,
        "refined": False
    })

    print("\n" + "="*60)
    print("EXECUTION SUMMARY")
    print("="*60)
    print(f"Refine passes: {result['refine_count']}")
    print(f"Refined: {result['refined']}")

    print("\n" + "="*60)
    print("REVIEW FEEDBACK")
    print("="*60)
    print(result["review_feedback"])

    print("\n" + "="*60)
    print("FINAL TEST CASES")
    print("="*60)
    print(result["final_test_cases"] or result["test_cases"])

    