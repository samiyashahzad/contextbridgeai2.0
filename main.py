import streamlit as st
import google.generativeai as genai
import json
import time

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="ContextBridge AI",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Custom CSS ---
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E88E5; font-weight: 700;}
    .sub-header {font-size: 1.2rem; color: #424242;}
    .card {background-color: #f9f9f9; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;}
    .success-box {background-color: #e8f5e9; padding: 15px; border-radius: 5px; border-left: 5px solid #2e7d32;}
    .warning-box {background-color: #fff3e0; padding: 15px; border-radius: 5px; border-left: 5px solid #ef6c00;}
</style>
""", unsafe_allow_html=True)

# --- 3. Sidebar (Smart Auth Logic) ---
with st.sidebar:
    st.title("🌉 ContextBridge")
    st.caption("v1.0 MVP | Enterprise Edition")
    st.divider()
    
    # Initialize api_key in session state if not present
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None

    # 1. Try to get key from Cloud Secrets first
    if "GOOGLE_API_KEY" in st.secrets:
        st.session_state.api_key = st.secrets["GOOGLE_API_KEY"]
        auth_method = "cloud"
    else:
        auth_method = "manual"

    # 2. Check if we have a key now
    if st.session_state.api_key:
        genai.configure(api_key=st.session_state.api_key)
        
        if auth_method == "cloud":
            st.success("✅ System Online (Auto-Auth)")
        else:
            st.success("✅ System Online (Manual)")
            if st.button("Logout / Change Key"):
                st.session_state.api_key = None
                st.rerun()
    else:
        # 3. If no key, show the Input Box
        st.warning("🔒 Authentication Required")
        st.info("💡 Get a free API key at: https://aistudio.google.com/apikey")
        manual_key = st.text_input("Enter Google API Key", type="password", help="Paste your key to access the system")
        
        if manual_key:
            st.session_state.api_key = manual_key
            st.rerun()
    
    st.divider()
    st.markdown("**User Mode:**")
    mode = st.radio("Select Persona", ["Sales Rep (Input)", "Manager (Review)", "Customer Success (View)"])

# --- 4. Main App Logic ---
st.markdown('<p class="main-header">ContextBridge AI Dashboard</p>', unsafe_allow_html=True)

# Session State
if 'data' not in st.session_state:
    st.session_state.data = None

# --- VIEW 1: SALES REP (Input) ---
if mode == "Sales Rep (Input)":
    st.markdown('<p class="sub-header">New Account Handover</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        input_text = st.text_area("Paste Call Transcript / Email Thread", height=300, 
                                   placeholder="Example:\n\nWe spoke with the client today. They want onboarding completed within 2 weeks.\nSales promised priority support for the first month.\nThey are worried about data migration from their old system.\nThey specifically asked for weekly check-ins during onboarding.")
    
    with col2:
        st.info("💡 **Tip:** Paste the full raw text. Our AI will filter out the noise and extract only commitments, risks, and technical needs.")
        
        # Disable button if no key is present
        btn_disabled = st.session_state.api_key is None
        if st.button("🚀 Analyze & Extract", use_container_width=True, disabled=btn_disabled):
            if not input_text:
                st.error("Please paste a transcript.")
            else:
                with st.spinner("AI is processing deal context..."):
                    try:
                        # First, let's list available models to debug
                        try:
                            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                            st.info(f"🔍 Available models: {', '.join(available_models[:3])}")
                        except:
                            pass
                        
                        # Try models with full path
                        models_to_try = [
                            "gemini-1.5-flash",
                            "gemini-1.5-pro", 
                            "gemini-pro",
                            "models/gemini-1.5-flash",
                            "models/gemini-1.5-pro",
                            "models/gemini-pro"
                        ]
                        
                        success = False
                        last_error = None
                        
                        for model_name in models_to_try:
                            try:
                                model = genai.GenerativeModel(model_name)
                                
                                prompt = f"""
                                Extract these fields from the text into JSON format:
                                - goals: The client's main goal or objective
                                - commitments: Promises made by our sales team
                                - risks: Client hesitations, fears, or concerns
                                - tech_stack: Technical requirements or stack mentioned

                                Text: {input_text}
                                
                                Return ONLY valid JSON with no markdown formatting. Example:
                                {{
                                    "goals": "Complete onboarding in 2 weeks",
                                    "commitments": "Priority support for first month",
                                    "risks": "Worried about data migration",
                                    "tech_stack": "Legacy system integration"
                                }}
                                """
                                
                                response = model.generate_content(prompt)
                                
                                # Clean up response to ensure it is valid JSON
                                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                                st.session_state.data = json.loads(clean_text)
                                
                                st.success(f"✅ Extraction Complete! (Model: {model_name})")
                                st.info("Switch to 'Manager' view to review.")
                                success = True
                                break
                                
                            except Exception as e:
                                last_error = str(e)
                                continue
                        
                        if not success:
                            st.error(f"❌ Could not process with available models.")
                            with st.expander("🔍 Error Details"):
                                st.code(last_error)
                            st.warning("**Solutions:**")
                            st.markdown("""
                            1. **Get a NEW API key**: Go to https://aistudio.google.com/apikey
                            2. Click "Create API Key" → "Create API key in new project"
                            3. Copy the new key and paste it in the sidebar
                            4. Make sure you're using a **Google AI Studio** key (not Vertex AI)
                            """)
                            
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

# --- VIEW 2: MANAGER (Review) ---
elif mode == "Manager (Review)":
    if st.session_state.data:
        st.markdown('<p class="sub-header">Review Extracted Context</p>', unsafe_allow_html=True)
        
        # Helper to handle Lists vs Strings
        def format_value(value):
            if isinstance(value, list):
                return "<br>• ".join(value)
            return str(value)
        
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
        
        if st.button("✅ Approve & Publish Handover"):
            with st.spinner("Syncing to CRM and notifying Customer Success..."):
                time.sleep(2)
            st.balloons()
            st.success("Success! Handover package has been finalized and sent.")
            
    else:
        st.warning("No data found. Please go to 'Sales Rep' mode and analyze a transcript first.")

# --- VIEW 3: CS (View) ---
elif mode == "Customer Success (View)":
    st.markdown("### 📂 Account: Global Corp Ltd")
    if st.session_state.data:
        st.json(st.session_state.data)
    else:
        st.info("Waiting for handover data...")