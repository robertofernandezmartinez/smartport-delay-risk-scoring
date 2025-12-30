import streamlit as st
import google.generativeai as genai
import os

# 1. Setup - Replace with your actual Gemini API Key
os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="SmartPort AI Chat", page_icon="🚢")
st.title("🚢 SmartPort AI: Harbor Assistant")
st.markdown("Ask me about vessel risks or operational instructions.")

# 2. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Chat Input
if prompt := st.chat_input("How can I help with port operations today?"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Gemini Response
    with st.chat_message("assistant"):
        # You can inject context here (e.g., "You are an expert port controller...")
        response = model.generate_content(prompt)
        full_response = response.text
        st.markdown(full_response)
    
    # Save Assistant response
    st.session_state.messages.append({"role": "assistant", "content": full_response})