import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import SentenceTransformerEmbeddings

load_dotenv()

# ── 1. Load PDFs ──────────────────────────────────────────
def load_documents(data_folder="data"):
    docs = []
    for file in os.listdir(data_folder):
        if file.endswith(".pdf"):
            print(f"Loading: {file}")
            loader = PyPDFLoader(os.path.join(data_folder, file))
            docs.extend(loader.load())
    print(f"Total pages loaded: {len(docs)}")
    return docs

# ── 2. Split into chunks ──────────────────────────────────
def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(docs)
    print(f"Total chunks created: {len(chunks)}")
    return chunks

# ── 3. Create vector store (local embeddings — no API cost) ──
def create_vectorstore(chunks):
    embeddings = SentenceTransformerEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="chroma_db"
    )
    print("Vector store created.")
    return vectorstore

# ── 4. Build RAG chain ────────────────────────────────────
def build_qa_chain(vectorstore):
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0.2,
        max_tokens=1024
    )

    # Increase chunks retrieved for broad questions
    retriever = vectorstore.as_retriever(
    search_type="mmr",  # Maximum Marginal Relevance — better for broad questions
    search_kwargs={"k": 6, "fetch_k": 20}
    )


    prompt = ChatPromptTemplate.from_template("""
    You are an expert on the Australian Federal Budget 2026-27.
    Answer the question using only the context provided below.
    If the answer is not in the context, say "I could not find this in the budget documents."
    
    Context:
    {context}
    
    Question: {question}

     Answer:""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever

# ── 5. Ask a question ─────────────────────────────────────
def ask(chain, retriever, question):
    print(f"\nQ: {question}")
    answer = chain.invoke(question)
    print(f"A: {answer}")
    sources = retriever.invoke(question)
    print(f"Sources used: {len(sources)} chunks")
    return answer, sources

def evaluate_retrieval_quality(question, source_docs):
    """
    Did we actually retrieve relevant chunks?
    Check if key question words appear in retrieved context.
    """
    question_keywords = [w.lower() for w in question.split() 
                        if len(w) > 4 and w.lower() not in 
                        ["what", "which", "where", "there", "their", "about", "budget"]]
    
    context_text = " ".join([doc.page_content.lower() for doc in source_docs])
    
    matches = [k for k in question_keywords if k in context_text]
    score = len(matches) / len(question_keywords) if question_keywords else 0
    
    return {
        "score": round(score, 2),
        "keywords_searched": question_keywords,
        "keywords_found": matches,
        "verdict": "GOOD retrieval" if score > 0.5 else "POOR retrieval — chunks may be irrelevant"
    }

def evaluate_faithfulness(answer, source_docs):
    """
    Simple faithfulness check — does the answer contain
    key phrases from the retrieved source chunks?
    """
    source_text = " ".join([doc.page_content.lower() for doc in source_docs])
    answer_words = [w.lower() for w in answer.split() if len(w) > 5]
    
    matches = sum(1 for word in answer_words if word in source_text)
    score = matches / len(answer_words) if answer_words else 0
    return round(min(score * 2, 1.0), 2)  # normalize to 0-1

def evaluate_hallucination(answer):
    """
    Simple hallucination flag — did the model admit uncertainty
    or did it confidently answer without grounding?
    """
    uncertainty_phrases = [
        "i could not find",
        "not mentioned",
        "not in the document",
        "no information",
        "unclear from"
    ]
    answer_lower = answer.lower()
    flagged = any(phrase in answer_lower for phrase in uncertainty_phrases)
    return "appropriate uncertainty" if flagged else "confident answer"

def run_evaluation(chain, retriever):
    print("\n" + "="*50)
    print("AI QUALITY EVALUATION REPORT")
    print("="*50)

    test_cases = [
        {
            "question": "What is the projected budget deficit or surplus for 2026-27?",
            "expected_keywords": ["billion", "surplus", "deficit", "budget"]
        },
        {
            "question": "What cost of living relief measures are in the 2026-27 budget?",
            "expected_keywords": ["energy", "relief", "household", "cost"]
        },
        {
            "question": "How much funding is allocated to housing in the 2026-27 budget?",
            "expected_keywords": ["housing", "billion", "million", "homes"]
        },
        {
            "question": "What did the budget say about cryptocurrency?",
            "expected_keywords": []  # should NOT be in budget — hallucination test
        },
    ]

    results = []

    for tc in test_cases:
        q = tc["question"]
        answer = chain.invoke(q)
        source_docs = retriever.invoke(q)

        # Faithfulness score
        faithfulness = evaluate_faithfulness(answer, source_docs)

        # Keyword coverage
        answer_lower = answer.lower()
        keywords_found = [k for k in tc["expected_keywords"] if k in answer_lower]
        keyword_score = len(keywords_found) / len(tc["expected_keywords"]) if tc["expected_keywords"] else "N/A (hallucination test)"

        # Hallucination check
        hallucination = evaluate_hallucination(answer)

        result = {
            "question": q,
            "answer": answer[:150] + "..." if len(answer) > 150 else answer,
            "faithfulness": faithfulness,
            "keyword_coverage": keyword_score,
            "hallucination_flag": hallucination
        }
        results.append(result)

        retrieval = evaluate_retrieval_quality(q, source_docs)
        print(f"Retrieval quality  : {retrieval['score']} — {retrieval['verdict']}")

        print(f"\nQ: {q}")
        print(f"A: {result['answer']}")
        print(f"Faithfulness score : {faithfulness}")
        print(f"Keyword coverage   : {keyword_score}")
        print(f"Hallucination flag : {hallucination}")
        print("-" * 50)

    # Summary
    faith_scores = [r["faithfulness"] for r in results]
    avg_faith = round(sum(faith_scores) / len(faith_scores), 2)
    print(f"\nOVERALL AVERAGE FAITHFULNESS: {avg_faith}")
    print("="*50)

    return results

# ── Main ──────────────────────────────────────────────────
if __name__ == "__main__":
    docs = load_documents()
    chunks = split_documents(docs)
    vectorstore = create_vectorstore(chunks)
    chain, retriever = build_qa_chain(vectorstore)

    questions = [
        "What is the projected budget deficit for 2026-27?",
        "What are the key cost of living measures in the 2026-27 budget?",
        "How much is allocated to housing in the 2026-27 budget?",
    ]

    for q in questions:
        ask(chain, retriever, q)
        run_evaluation(chain, retriever)