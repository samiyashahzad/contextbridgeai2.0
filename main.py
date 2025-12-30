import streamlit as st
import google.generativeai as genai
import json

# --- 1. Page Configuration (Makes it look like a real product) ---
st.set_page_config(
    page_title="ContextBridge AI",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Custom CSS (To make it look fancy/expensive) ---
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E88E5; font-weight: 700;}
    .sub-header {font-size: 1.2rem; color: #424242;}
    .card {background-color: #f9f9f9; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;}
    .success-box {background-color: #e8f5e9; padding: 15px; border-radius: 5px; border-left: 5px solid #2e7d32;}
    .warning-box {background-color: #fff3e0; padding: 15px; border-radius: 5px; border-left: 5px solid #ef6c00;}
</style>
""", unsafe_allow_html=True)

# --- 3. Sidebar (Your "App Controls") ---
with st.sidebar:
    st.title("🌉 ContextBridge")
    st.caption("v1.0 MVP | Enterprise Edition")
    st.divider()
    
    api_key = st.text_input("🔑 Google API Key", type="password", help="Paste your Gemini API key here")
    
    if api_key:
        genai.configure(api_key=api_key)
        st.success("System Online")
    else:
        st.warning("Waiting for Key...")
    
    st.divider()
    st.markdown("**User Mode:**")
    mode = st.radio("Select Persona", ["Sales Rep (Input)", "Manager (Review)", "Customer Success (View)"])

# --- 4. Main App Logic ---
st.markdown('<p class="main-header">ContextBridge AI Dashboard</p>', unsafe_allow_html=True)

# Session State to hold data between clicks
if 'data' not in st.session_state:
    st.session_state.data = None

# --- VIEW 1: SALES REP (Input) ---
if mode == "Sales Rep (Input)":
    st.markdown('<p class="sub-header">New Account Handover</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        input_text = st.text_area("Paste Call Transcript / Email Thread", height=300)
    
    with col2:
        st.info("💡 **Tip:** Paste the full raw text. Our AI will filter out the noise and extract only commitments, risks, and technical needs.")
        if st.button("🚀 Analyze & Extract", use_container_width=True):
            if not api_key:
                st.error("Please enter API Key in sidebar.")
            elif not input_text:
                st.error("Please paste a transcript.")
            else:
                with st.spinner("AI is processing deal context..."):
                    try:
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        prompt = f"""
                        Extract these fields from the text into JSON:
                        - goals (The client's main goal)
                        - commitments (Promises made by us)
                        - risks (Client hesitations/fears)
                        - tech_stack (Technical requirements)
                        
                        Text: {input_text}
                        Return JSON only.
                        """
                        response = model.generate_content(prompt)
                        clean_json = response.text.replace("```json", "").replace("```", "")
                        st.session_state.data = json.loads(clean_json)
                        st.success("Extraction Complete! Switch to 'Manager' view to review.")
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- VIEW 2: MANAGER (Review) ---
elif mode == "Manager (Review)":
    if st.session_state.data:
        st.markdown('<p class="sub-header">Review Extracted Context</p>', unsafe_allow_html=True)
        
        # --- HELPER FUNCTION: Fixes the "List" error ---
        def format_value(value):
            if isinstance(value, list):
                return ", ".join(value)  # Joins list items with commas
            return str(value)            # Keeps text as text
        
        # Get data safely
        goals = format_value(st.session_state.data.get('goals', 'N/A'))
        risks = format_value(st.session_state.data.get('risks', 'N/A'))
        commitments = format_value(st.session_state.data.get('commitments', 'N/A'))
        tech = format_value(st.session_state.data.get('tech_stack', 'N/A'))

        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="card"><b>🎯 Client Goals</b><br>{goals}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="warning-box"><b>⚠️ Identified Risks</b><br>{risks}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="success-box"><b>🤝 Commitments Made</b><br>{commitments}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="card"><b>💻 Tech Stack</b><br>{tech}</div>', unsafe_allow_html=True)
        
        st.button("✅ Approve & Publish Handover")
    else:
        st.warning("No data found. Please go to 'Sales Rep' mode and analyze a transcript first.")
# --- VIEW 3: CS (View) ---
elif mode == "Customer Success (View)":
    st.markdown("### 📂 Account: Global Corp Ltd")
    if st.session_state.data:
        st.json(st.session_state.data)
    else:
        st.info("Waiting for handover data...")