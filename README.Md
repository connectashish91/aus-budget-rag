# Australian Budget 2026-27 RAG App

A Retrieval-Augmented Generation (RAG) application that answers questions 
about the Australian Federal Budget 2026-27, built with LangChain and Claude.

## What This Demonstrates
- RAG pipeline design and implementation
- AI output evaluation (faithfulness, hallucination detection, retrieval quality)
- Prompt engineering for domain-specific Q&A
- QA-first approach to LLM applications

## Tech Stack
- LangChain (LCEL pipeline)
- Anthropic Claude Haiku
- ChromaDB (vector store)
- SentenceTransformers (local embeddings)
- Python 3.14

## AI Quality Evaluation
This app includes a built-in evaluation framework that measures:
- **Faithfulness** — is the answer grounded in the source document?
- **Hallucination detection** — does the model admit uncertainty appropriately?
- **Retrieval quality** — did the vector store return relevant chunks?
- **Keyword coverage** — does the answer contain expected domain terms?

## Sample Results
| Question | Faithfulness | Hallucination |
|---|---|---|
| Housing allocation | 1.0 | Confident (correct) |
| Cryptocurrency (not in doc) | 0.83 | Appropriate uncertainty |
| Cost of living measures | 0.57 | Appropriate uncertainty |

## Setup
```bash
git clone https://github.com/YOUR_USERNAME/aus-budget-rag
cd aus-budget-rag
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your API key to `.env`: