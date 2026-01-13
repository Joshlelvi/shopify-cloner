import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Shopify Cloner Chat", page_icon="💬", layout="wide")

# --- CSS FOR BETTER UI ---
st.markdown("""
<style>
    .stChatMessage { background-color: #f0f2f6; border-radius: 10px; padding: 10px; }
    .stChatMessage[data-testid="stChatMessageUser"] { background-color: #e8f5e9; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SETTINGS & INPUTS ---
with st.sidebar:
    st.header("⚙️ Setup")
    api_key = st.text_input("Gemini API Key", type="password")
    model_choice = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
    
    st.divider()
    st.subheader("📸 Context")
    uploaded_image = st.file_uploader("Upload Settings Screenshot", type=["jpg", "png", "jpeg"])
    if uploaded_image:
        st.image(uploaded_image, caption="Settings Reference", use_container_width=True)

    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chat = None
        st.rerun()

# --- INITIALIZE CHAT SESSION ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SYSTEM PROMPT (The Brain) ---
SYSTEM_INSTRUCTION = """
You are an expert Shopify Theme Developer. 
Your goal is to help the user clone Shopify Sections from HTML/CSS and Screenshots.
- ALWAYS output clean Liquid code.
- If the user provides HTML, convert it to a dynamic Section with Schema.
- If the user asks for a change (e.g., "Make the title bigger"), ONLY modify the relevant parts or rewrite the code if necessary.
- Remember: Use {% schema %} for settings and CSS variables for styles.
"""

def get_gemini_response(user_input, image=None):
    if not api_key:
        return "⚠️ Please enter your API Key in the sidebar."
    
    genai.configure(api_key=api_key)
    
    # Initialize chat if not exists
    if "chat" not in st.session_state or st.session_state.chat is None:
        model = genai.GenerativeModel(model_choice, system_instruction=SYSTEM_INSTRUCTION)
        st.session_state.chat = model.start_chat(history=[])

    try:
        # If an image is uploaded, we send it along with the text
        if image:
            img = Image.open(image)
            response = st.session_state.chat.send_message([user_input, img])
        else:
            response = st.session_state.chat.send_message(user_input)
            
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- MAIN CHAT INTERFACE ---
st.title("💬 Shopify Section Cloner Chat")
st.caption("Paste your HTML/CSS below, or ask for modifications.")

# 1. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "```" in message["content"]:
            st.code(message["content"].replace("```liquid", "").replace("```", ""), language="liquid")
        else:
            st.markdown(message["content"])

# 2. Handle User Input
if prompt := st.chat_input("Paste HTML code here or ask for a change..."):
    # Add User Message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Coding..."):
            response_text = get_gemini_response(prompt, uploaded_image)
            
            # Smart Formatting: If it looks like code, use st.code
            if "```" in response_text or "{% schema %}" in response_text:
                clean_code = response_text.replace("```liquid", "").replace("```html", "").replace("```", "")
                st.code(clean_code, language="liquid")
            else:
                st.markdown(response_text)
    
    # Add AI Response to History
    st.session_state.messages.append({"role": "assistant", "content": response_text})