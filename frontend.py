import streamlit as st
import requests
import uuid

API_URL = "http://localhost:8000"

st.set_page_config(page_title="MirAI Policy Advisor", page_icon="🎓", layout="centered")

# CSS for a modern, minimal, premium interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* Typography & Colors */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #0f172a; /* Dark navy text */
    }
    .stApp {
        background-color: #fdfdfc; /* Warm white */
    }

    /* Minimalist header */
    .brand-header {
        text-align: center;
        padding-top: 4rem;
        padding-bottom: 2rem;
    }
    .brand-header h1 {
        font-weight: 600;
        font-size: 2.5rem;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }
    .brand-header p {
        color: #64748b;
        font-size: 1.1rem;
    }

    /* Buttons / Chips */
    div.stButton > button {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
        color: #0f172a;
        font-weight: 500;
        transition: all 0.2s ease;
        padding: 0.5rem 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    div.stButton > button:hover {
        border-color: #0d9488; /* Teal accent */
        color: #0d9488;
        background-color: #f0fdfa;
        box-shadow: 0 4px 6px rgba(13, 148, 136, 0.1);
    }
    div.stButton > button:focus:not(:focus-visible) {
        color: #0d9488;
    }

    /* Primary actions */
    div.stButton > button[kind="primary"] {
        background-color: #0d9488;
        color: white;
        border: none;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #0f766e;
        color: white;
    }

    /* Suggestion tiles container */
    .suggestion-title {
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
        color: #0f172a;
    }
    .suggestion-desc {
        font-size: 0.8rem;
        color: #64748b;
        white-space: normal;
        text-align: left;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    .sidebar-title {
        font-weight: 600;
        color: #334155;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }

    /* Status indicator */
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-dot.offline {
        background-color: #ef4444;
    }
    .status-text {
        font-size: 0.85rem;
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)

# State initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"
if "current_question" not in st.session_state:
    st.session_state.current_question = None

# Backend health check
@st.cache_data(ttl=10)
def check_backend():
    try:
        res = requests.get(f"{API_URL}/health", timeout=2)
        return res.status_code == 200
    except:
        return False

is_backend_up = check_backend()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### 🎓 MirAI Advisor")
    
    # Status indicator
    if is_backend_up:
        st.markdown('<div class="status-text"><span class="status-dot"></span>System Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-text"><span class="status-dot offline"></span>Status unavailable</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation
    if st.button("💬 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_view = "chat"
        st.rerun()
        
    if st.button("📚 Manage Knowledge Base", use_container_width=True):
        st.session_state.current_view = "admin"
        st.rerun()
        
    st.markdown('<div class="sidebar-title">Explore Policies</div>', unsafe_allow_html=True)
    topics = {
        "Attendance & Evaluation": "I have 72% attendance. How many marks will I receive?",
        "Medical & Duty Leave": "I am sick. What is the medical leave submission process?",
        "Examinations & Malpractice": "What are the examination and malpractice rules?",
        "No Dues & Admit Cards": "What happens if I don't clear my dues?",
        "Code of Conduct": "What is the dress code policy?",
        "Clubs & Events": "How can we propose a new student society?"
    }
    
    for topic_name, question_text in topics.items():
        if st.button(topic_name, key=f"topic_{topic_name}", use_container_width=True):
            st.session_state.current_view = "chat"
            st.session_state.current_question = question_text
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div style="font-size: 0.75rem; color: #94a3b8; text-align: center;">Source: Mirai School of Technology<br>Student Policy Handbook 2026</div>', unsafe_allow_html=True)

# ----------------- MAIN AREA -----------------
if st.session_state.current_view == "admin":
    st.subheader("Manage Knowledge Base")
    st.markdown("Upload the official student policy handbook PDF to update the system's authoritative knowledge source.")
    
    uploaded_file = st.file_uploader("Upload Handbook PDF", type=["pdf"])
    if st.button("Ingest PDF", type="primary"):
        if uploaded_file is not None:
            if not is_backend_up:
                st.error("Backend is unavailable. Cannot ingest document.")
            else:
                with st.spinner("Analyzing and updating knowledge base..."):
                    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                    try:
                        res = requests.post(f"{API_URL}/ingest", files=files)
                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"Successfully processed {data['page_count']} pages into {data['chunk_count']} policy fragments.")
                        else:
                            st.error(f"Failed to ingest: {res.text}")
                    except Exception as e:
                        st.error(f"Ingestion failed: {str(e)}")
        else:
            st.warning("Please select a PDF file first.")
            
elif st.session_state.current_view == "chat":
    # Empty state / Welcome screen
    if not st.session_state.messages:
        st.markdown("""
        <div class="brand-header">
            <h1>MirAI Policy Advisor</h1>
            <p>Clear answers. Official policies. Trusted sources.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; color: #475569; margin-bottom: 2rem;'>Ask me anything about grading, attendance, clubs, or campus rules based on the 2026 Student Handbook.</p>", unsafe_allow_html=True)
        
        # Suggestions Grid
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 **Attendance & Marks**\n\nI have 72% attendance. How many marks will I receive?", use_container_width=True):
                st.session_state.current_question = "I have 72% attendance. How many marks will I receive?"
                st.rerun()
            if st.button("👥 **Clubs & Societies**\n\nHow can we propose a new student society?", use_container_width=True):
                st.session_state.current_question = "How can we propose a new student society?"
                st.rerun()
        with col2:
            if st.button("🏥 **Medical Leave**\n\nI am sick. What is the medical leave submission process?", use_container_width=True):
                st.session_state.current_question = "I am sick. What is the medical leave submission process?"
                st.rerun()
            if st.button("📝 **Examination Rules**\n\nWhat are the examination and malpractice rules?", use_container_width=True):
                st.session_state.current_question = "What are the examination and malpractice rules?"
                st.rerun()
                
    else:
        # Render chat history
        for idx, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"], avatar="🎓" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])
                
                # Show sources if assistant
                if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
                    with st.expander("View Source Evidence"):
                        for src in msg["sources"]:
                            st.markdown(f"**Page {src.get('page', '?')}**")
                            st.markdown(f"> *{src.get('content', '')}*")
                            st.markdown("---")
                            
                # Feedback & utilities (only on latest assistant message)
                if msg["role"] == "assistant" and idx == len(st.session_state.messages) - 1:
                    f_col1, f_col2, f_col3 = st.columns([1, 1, 6])
                    with f_col1:
                        st.button("👍 Helpful", key=f"up_{idx}")
                    with f_col2:
                        st.button("👎 Poor", key=f"down_{idx}")

    # Chat Input
    question = st.chat_input("Ask a policy question...")
    
    # Process question from input or suggestion click
    if st.session_state.current_question:
        question = st.session_state.current_question
        st.session_state.current_question = None

    if question:
        if not is_backend_up:
            st.error("Cannot connect to the MirAI backend. Please check system status.")
        else:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user", avatar="👤"):
                st.markdown(question)
                
            # Generate assistant response
            with st.chat_message("assistant", avatar="🎓"):
                with st.spinner("Consulting official policies..."):
                    try:
                        res = requests.post(f"{API_URL}/chat", json={"question": question})
                        if res.status_code == 200:
                            data = res.json()
                            if data.get("error"):
                                answer = f"**I was unable to verify that policy.**\n\n{data['error']}"
                                sources = []
                            else:
                                answer = data["answer"]
                                sources = data.get("sources", [])
                            
                            st.markdown(answer)
                            
                            if sources:
                                with st.expander("View Source Evidence"):
                                    for src in sources:
                                        st.markdown(f"**Page {src.get('page', '?')}**")
                                        st.markdown(f"> *{src.get('content', '')}*")
                                        st.markdown("---")
                            
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": answer, 
                                "sources": sources
                            })
                            st.rerun()
                        else:
                            try:
                                error_detail = res.json().get('detail', res.text)
                            except:
                                error_detail = res.text
                                
                            if "429" in error_detail or "Quota" in error_detail or "ResourceExhausted" in error_detail:
                                st.error("Google API Rate Limit Exceeded: The free tier allows only 5 requests per minute. Please wait 1 minute and try your question again.")
                            elif "504" in error_detail or "DeadlineExceeded" in error_detail:
                                st.error("Google API Timeout: The Google servers are currently slow and the request timed out. Please try again.")
                            else:
                                st.error(f"System Error: {error_detail}")
                                
                    except requests.exceptions.ConnectionError:
                        st.error("Backend not reachable. Please start the FastAPI server.")
