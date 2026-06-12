import streamlit as st
import json
from datetime import datetime
from app import load_documents, split_documents, create_vectorstore, build_qa_chain, evaluate_faithfulness, evaluate_hallucination, evaluate_retrieval_quality

st.title("🇦🇺 Australian Budget 2026-27 Q&A")
st.caption("Ask questions about the Australian Federal Budget — with AI quality evaluation")

@st.cache_resource
def load_chain():
    import os
    if os.path.exists("chroma_db"):
        # Vector store exists — skip document loading
        vectorstore = create_vectorstore()
    else:
        # First time — build from documents
        docs = load_documents()
        chunks = split_documents(docs)
        vectorstore = create_vectorstore(chunks)
    
    chain, retriever = build_qa_chain(vectorstore)
    return chain, retriever

def log_interaction(question, answer, faith_score, retrieval_score):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer_length": len(answer),
        "faithfulness": faith_score,
        "retrieval_quality": retrieval_score,
        "session_id": str(id(st.session_state))
    }
    with open("quality_log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

chain, retriever = load_chain()

# ── Rate limiting ─────────────────────────────────────────
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

st.sidebar.metric("Questions asked", st.session_state.query_count)

if st.session_state.query_count >= 10:
    st.warning("Demo limit reached — maximum 10 questions per session.")
    st.stop()


question = st.text_input("Ask a budget question:", placeholder="What is allocated to housing?")

if question:
    st.session_state.query_count += 1
    
    with st.spinner("Searching budget documents..."):
        answer = chain.invoke(question)
        sources = retriever.invoke(question)
        
        # Show answer
        st.markdown("### Answer")
        st.write(answer)
        
        # Show evaluation scores
        st.markdown("### Quality Evaluation")
        col1, col2, col3 = st.columns(3)
        
        faith = evaluate_faithfulness(answer, sources)
        halluc = evaluate_hallucination(answer)
        retrieval = evaluate_retrieval_quality(question, sources)
        
        log_interaction(question, answer, faith, retrieval["score"])

        col1.metric("Faithfulness", faith)
        col2.metric("Retrieval Quality", retrieval["score"])
        col3.metric("Hallucination Check", "Grounded ✅" if "confident" in halluc else "Uncertain ⚠️")
        
        # Show sources
        with st.expander("View source chunks"):
            for i, doc in enumerate(sources):
                st.markdown(f"**Chunk {i+1}**")
                st.text(doc.page_content[:300] + "...")