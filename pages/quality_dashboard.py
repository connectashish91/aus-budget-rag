import streamlit as st
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

st.title("📊 Quality Trend Dashboard")
st.caption("Monitoring AI output quality over time")

# ── Load log file ─────────────────────────────────────────
log_file = Path("quality_log.jsonl")

if not log_file.exists():
    st.warning("No quality log found yet. Ask some questions in the main app first.")
    st.stop()

# Parse log entries
entries = []
with open(log_file, "r") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

if not entries:
    st.warning("Log file is empty. Ask some questions in the main app first.")
    st.stop()

df = pd.DataFrame(entries)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

# ── Summary metrics ───────────────────────────────────────
st.markdown("### Overall Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Questions", len(df))
col2.metric("Avg Faithfulness", round(df["faithfulness"].mean(), 2))
col3.metric("Avg Retrieval Quality", round(df["retrieval_quality"].mean(), 2))
col4.metric("Avg Answer Length", round(df["answer_length"].mean(), 0))

st.divider()

# ── Faithfulness trend ────────────────────────────────────
st.markdown("### Faithfulness Score Over Time")
st.line_chart(df.set_index("timestamp")["faithfulness"])

# ── Retrieval quality trend ───────────────────────────────
st.markdown("### Retrieval Quality Over Time")
st.line_chart(df.set_index("timestamp")["retrieval_quality"])

# ── Score distribution ────────────────────────────────────
st.markdown("### Score Distribution")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Faithfulness**")
    st.bar_chart(df["faithfulness"].value_counts().sort_index())
with col2:
    st.markdown("**Retrieval Quality**")
    st.bar_chart(df["retrieval_quality"].value_counts().sort_index())

# ── Low quality alerts ────────────────────────────────────
st.markdown("### Low Quality Alerts")
low_quality = df[
    (df["faithfulness"] < 0.6) | (df["retrieval_quality"] < 0.5)
][["timestamp", "question", "faithfulness", "retrieval_quality"]]

if low_quality.empty:
    st.success("No low quality responses detected.")
else:
    st.warning(f"{len(low_quality)} low quality responses detected")
    st.dataframe(low_quality, use_container_width=True)

# ── Full log ──────────────────────────────────────────────
with st.expander("View full interaction log"):
    display_df = df[["timestamp", "question", "faithfulness",
                      "retrieval_quality", "answer_length"]].copy()
    display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(display_df, use_container_width=True)

# ── Drift detection ───────────────────────────────────────
if len(df) >= 5:
    st.markdown("### Drift Detection")
    recent = df.tail(5)["faithfulness"].mean()
    overall = df["faithfulness"].mean()
    drift = round(overall - recent, 2)

    if drift > 0.1:
        st.error(f"⚠️ Quality drift detected — recent faithfulness ({round(recent, 2)}) "
                 f"is lower than overall average ({round(overall, 2)})")
    elif drift < -0.1:
        st.success(f"✅ Quality improving — recent faithfulness ({round(recent, 2)}) "
                   f"is higher than overall average ({round(overall, 2)})")
    else:
        st.info(f"✅ Quality stable — no significant drift detected")