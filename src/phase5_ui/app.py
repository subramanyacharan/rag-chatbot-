import streamlit as st
import os
from src.phase3_rag_engine.generator import RAGGenerator

# Page configuration
st.set_page_config(
    page_title="Mutual Fund FAQ Assistant",
    page_icon="📈",
    layout="centered"
)

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stAlert {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and Disclaimer
st.title("📊 Mutual Fund FAQ Assistant")
st.markdown("### *Your factual guide to HDFC Mutual Fund Schemes*")

st.warning("⚠️ **Strict Disclaimer:** This assistant provides **factual information only** extracted from official scheme documents. It **DOES NOT** provide investment advice, recommendations, performance comparisons, or future predictions. Please consult a SEBI-registered financial advisor for investment decisions.")

# Initialize RAG Generator (Cached to avoid reloading model on every interaction)
@st.cache_resource
def get_generator():
    return RAGGenerator()

try:
    generator = get_generator()
except Exception as e:
    st.error(f"Failed to initialize RAG Engine: {e}")
    st.stop()

# Sidebar for example queries and info
with st.sidebar:
    st.header("Quick Links")
    st.info("This assistant is powered by a RAG (Retrieval-Augmented Generation) pipeline using ChromaDB and Groq Llama 3.")
    
    st.header("Example Queries")
    examples = [
        "What is the expense ratio of HDFC Mid-Cap Opportunities Fund?",
        "What is the exit load for HDFC Flexi Cap Fund?",
        "What is the lock-in period for ELSS Tax Saver Fund?",
        "Who is the fund manager for HDFC Top 100 Fund?",
        "What is the minimum SIP amount for HDFC Focused 30 Fund?"
    ]
    
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.query_input = ex

# Chat history state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
query = st.chat_input("Ask a factual question about HDFC Mutual Funds...")

# Handle sidebar button click by prioritizing it over chat_input
if "query_input" in st.session_state:
    query = st.session_state.query_input
    del st.session_state.query_input

if query:
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(query)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Retrieving verified facts..."):
            try:
                response = generator.generate_response(query)
                st.markdown(response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"An error occurred: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.divider()
st.caption("Data is refreshed daily via GitHub Actions. Last update check: today.")
