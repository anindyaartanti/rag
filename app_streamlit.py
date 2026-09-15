import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st
from config import GEMINI_MODEL, TEMPERATURE
from prompt import DISCLAIMER, format_sources_footer
from rag_pipeline import RAGPipeline

TOP_K = 5

BLUE = "#3760F9"
YELLOW = "#D2FC59"
WHITE = "#FFFFFF"
BLACK = "#000000"
GRAY = "#6B7280"

st.set_page_config(
    page_title="RAG Ketenagakerjaan Indonesia",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="expanded",
)

CSS = f"""
<style>

.stApp {{
    background: {WHITE};
    color: {BLACK};
}}

.main .block-container {{
    max-width: 900px;
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
}}

#MainMenu, footer {{ visibility: hidden; }}
header {{ background: transparent !important; }}

/* ---- SIDEBAR ---- */
section[data-testid="stSidebar"] {{
    background: {BLACK};
    border-right: none;
}}

section[data-testid="stSidebar"] * {{
    color: {WHITE};
}}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: {YELLOW};
}}

section[data-testid="stSidebar"] hr {{
    border-color: #333333;
}}

section[data-testid="stSidebar"] label {{
    color: {WHITE} !important;
}}

.sidebar-title {{
    font-size: 1.6rem;
    font-weight: 850;
    color: {YELLOW};
    margin-bottom: 0.3rem;
}}

.sidebar-subtitle {{
    color: #AAAAAA;
    font-size: 0.92rem;
    line-height: 1.5;
    margin-bottom: 1.5rem;
}}

.sidebar-info {{
    color: #CCCCCC;
    font-size: 0.9rem;
    line-height: 2;
}}

.sidebar-info b {{
    color: {WHITE};
    display: inline-block;
    min-width: 90px;
}}

.sidebar-disclaimer {{
    color: #999999;
    font-size: 0.82rem;
    line-height: 1.7;
}}

/* ---- STICKY HEADER ---- */
.app-header-wrapper {{
    position: sticky;
    top: 0;
    z-index: 999;
    background: {WHITE};
    padding: 1rem 0 0.6rem;
    margin-bottom: 0.5rem;
}}

.app-header {{
    text-align: center;
}}

.app-header h1 {{
    font-size: 1.6rem;
    font-weight: 800;
    color: {BLACK};
    margin: 0;
}}

.app-header h1 span {{
    color: {BLUE};
}}

.app-header p {{
    color: {GRAY};
    font-size: 0.88rem;
    margin: 0.3rem 0 0.8rem;
}}

.feature-row {{
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 0.4rem;
}}

.feature-tag {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #4B5563;
}}

.feature-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: {BLUE};
    flex-shrink: 0;
}}

/* ---- CHAT INPUT ---- */
[data-testid="stChatInput"] {{
    border: 2px solid {BLUE} !important;
    border-radius: 16px !important;
    background: {WHITE} !important;
}}

[data-testid="stChatInput"] textarea {{
    color: {BLACK} !important;
}}

[data-testid="stChatInput"] textarea::placeholder {{
    color: #9CA3AF !important;
}}

/* ---- CHAT MESSAGE ---- */
[data-testid="stChatMessage"] {{
    background: transparent !important;
    border: none !important;
    padding: 0.3rem 0 !important;
}}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
    line-height: 1.65;
}}

/* ---- EXPANDER ---- */
[data-testid="stExpander"] {{
    background: {WHITE};
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    margin-top: 0.5rem;
}}

[data-testid="stExpander"] summary {{
    color: {BLACK};
    font-weight: 700;
    font-size: 0.85rem;
}}

/* ---- BUTTON ---- */
.stButton > button {{
    background: {BLUE};
    color: {WHITE};
    border: none;
    border-radius: 10px;
    font-weight: 700;
}}

.stButton > button:hover {{
    background: #294DD0;
    color: {WHITE};
}}

/* ---- FOOTER ---- */
.app-footer {{
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #E5E7EB;
    text-align: center;
    color: {GRAY};
    font-size: 0.72rem;
}}

</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

if "pipeline" not in st.session_state:
    st.session_state.pipeline = None

with st.sidebar:

    st.markdown(
        f"""
        <div class="sidebar-title">⚖️ RAG Ketenagakerjaan</div>
        <div class="sidebar-subtitle">Asisten regulasi ketenagakerjaan Indonesia</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("ℹ️ Info Sistem")

    st.markdown(
        f"""
        <div class="sidebar-info">
            <b>LLM</b> {GEMINI_MODEL}<br>
            <b>Temperature</b> {TEMPERATURE}<br>
            <b>Top-k</b> {TOP_K} chunks<br>
            <b>Embedding</b> multilingual-e5-base<br>
            <b>Vector DB</b> ChromaDB · Cosine
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        f'<div class="sidebar-disclaimer">{DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )


@st.cache_resource
def load_pipeline():
    return RAGPipeline(top_k=TOP_K)


if st.session_state.pipeline is None:
    st.session_state.pipeline = load_pipeline()

pipeline = st.session_state.pipeline

st.markdown(
    """
    <div class="app-header-wrapper">
        <div class="app-header">
            <h1>⚖️ Chatbots: <span>RAG Ketenagakerjaan</span> Indonesia</h1>
            <p>Temukan informasi regulasi ketenagakerjaan melalui percakapan yang cepat dan berbasis dokumen.</p>
            <div class="feature-row">
                <span class="feature-tag"><span class="feature-dot"></span>11 dokumen regulasi</span>
                <span class="feature-tag"><span class="feature-dot"></span>Semantic retrieval</span>
                <span class="feature-tag"><span class="feature-dot"></span>Sumber terlampir</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📄 Sumber & Retrieved Chunks"):
                st.markdown("**Sumber yang dirujuk:**")
                st.text(msg["footer"])

                if msg.get("chunks"):
                    st.markdown("**Retrieved Chunks:**")
                    for i, c in enumerate(msg["chunks"], 1):
                        m = c.get("metadata", {})
                        st.markdown(
                            f"**[{i}]** `score={c.get('score', 0):.4f}` "
                            f"· `{m.get('document_id', '')}` · {m.get('pasal', '')}"
                        )
                        st.caption(c.get("text", "")[:300])
                        st.divider()

if user_query := st.chat_input("Tanyakan sesuatu tentang regulasi..."):

    with st.chat_message("user"):
        st.markdown(user_query)

    st.session_state.history.append({
        "role": "user",
        "content": user_query,
        "sources": [],
        "chunks": [],
        "footer": "",
    })

    with st.chat_message("assistant"):

        with st.spinner("Mencari regulasi yang relevan..."):
            result = pipeline.answer_question(user_query, k=TOP_K)
            answer = result["answer"]
            sources = result["sources"]
            chunks = result["retrieved_chunks"]
            footer = format_sources_footer(sources)

        st.markdown(answer)

        if sources:
            with st.expander("📄 Sumber & Retrieved Chunks"):
                st.markdown("**Sumber yang dirujuk:**")
                st.text(footer)

                st.markdown("**Retrieved Chunks:**")
                for i, c in enumerate(chunks, 1):
                    m = c.get("metadata", {})
                    st.markdown(
                        f"**[{i}]** `score={c.get('score', 0):.4f}` "
                        f"· `{m.get('document_id', '')}` · {m.get('pasal', '')}"
                    )
                    st.caption(c.get("text", "")[:300])
                    st.divider()

        st.session_state.history.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "chunks": chunks,
            "footer": footer,
        })

st.markdown(
    f"""
    <div class="app-footer">
        ⚖️ RAG Ketenagakerjaan Indonesia &nbsp;·&nbsp;
        Model: {GEMINI_MODEL} &nbsp;·&nbsp;
        Top-k: {TOP_K} &nbsp;·&nbsp;
        Embedding: multilingual-e5-base
    </div>
    """,
    unsafe_allow_html=True,
)
