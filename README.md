# 🇦🇺 Australian Budget 2026-27 — RAG App with AI Quality Evaluation

A **Retrieval-Augmented Generation (RAG)** application that answers natural language 
questions about the Australian Federal Budget 2026-27, built with a QA-first mindset.

This project demonstrates what happens when **11 years of quality engineering discipline 
meets AI systems** — not just building a RAG app, but building one with a proper 
evaluation framework that tests whether the AI is actually working correctly.

---

## 🎯 What Makes This Different

Most RAG demos just show that the app answers questions. This one also asks:
- Is the answer **faithful** to the source document?
- Did the model **hallucinate** or admit uncertainty appropriately?
- Did the vector store **retrieve the right chunks**?
- Does the answer contain the **expected domain terms**?

That's AI QA — and it's the missing layer in most AI products.

---

## 🏗️ Architecture

```
PDF Documents (Budget Papers 1 & 2)
        ↓
  PDF Loader (LangChain)
        ↓
  Text Chunker (RecursiveCharacterTextSplitter)
        ↓
  Local Embeddings (SentenceTransformers — free, no API cost)
        ↓
  Vector Store (ChromaDB — local)
        ↓
  Retriever (MMR search — top 4 chunks)
        ↓
  LLM (Anthropic Claude Haiku)
        ↓
  Answer + Evaluation Report
```

---

## 📊 Sample Evaluation Results

| Question | Faithfulness | Keyword Coverage | Hallucination Flag |
|---|---|---|---|
| Housing allocation ($4.3B) | 1.0 | 0.75 | Confident answer ✅ |
| Budget deficit projection | 0.92 | 0.75 | Appropriate uncertainty ✅ |
| Cost of living measures | 0.57 | 0.50 | Appropriate uncertainty ⚠️ |
| Cryptocurrency (not in doc) | 0.83 | N/A | Appropriate uncertainty ✅ |

**Overall average faithfulness: 0.79**

The cost of living result (0.57) is a known retrieval quality issue —
the chunking strategy misses some policy sections. This is documented
as a future improvement.

---

## 🧪 Evaluation Framework

Built-in evaluation covers three dimensions:

**1. Faithfulness Score (0–1)**
Measures whether the answer is grounded in retrieved source chunks.
A score of 1.0 means every key term in the answer exists in the source.

**2. Hallucination Detection**
Checks whether the model appropriately expresses uncertainty when
information is not in the document — vs confidently answering from context.

**3. Retrieval Quality Score (0–1)**
Measures whether the vector store retrieved chunks relevant to the question.
Low retrieval quality = the LLM never had a chance to answer correctly.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | Anthropic Claude Haiku |
| Orchestration | LangChain (LCEL pipeline) |
| Vector Store | ChromaDB (local) |
| Embeddings | SentenceTransformers all-MiniLM-L6-v2 (local, free) |
| Document Loading | LangChain PyPDFLoader |
| Language | Python 3.14 |

---

## ⚙️ Setup

```bash
git clone https://github.com/connectashish91/aus-budget-rag
cd aus-budget-rag
python -m venv venv
source venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
```

Create `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
```

Download Budget PDFs from [budget.gov.au](https://budget.gov.au) and place in `data/`:
- Budget Paper No. 1 (bp1_2026-27.pdf)
- Budget Paper No. 2 (bp2_2026-27.pdf)

Run the app:
```bash
python app.py
```

---

## 📁 Project Structure

```
aus-budget-rag/
├── app.py              # Main RAG application + evaluation framework
├── data/               # Budget PDFs (download separately from budget.gov.au)
├── requirements.txt    # Minimal dependencies
├── .gitignore
└── README.md
```

---

## 🔮 Planned Improvements

- [ ] Add Streamlit UI with visible evaluation scores
- [ ] Implement Promptfoo regression testing for prompt changes
- [ ] Improve cost of living retrieval with better chunking strategy
- [ ] Add quality trend logging across sessions (drift detection)
- [ ] Deploy to Hugging Face Spaces

---

## 👤 About

Built by **Ashish Kumar** — Senior Quality Engineer transitioning into AI/ML QA.  
11 years of quality engineering experience applied to AI systems.

[LinkedIn](https://linkedin.com/in/ashish-kumar-654b37158) • [GitHub](https://github.com/connectashish91)
