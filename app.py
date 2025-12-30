import streamlit as st
import google.generativeai as genai
import os

# --- 1. INITIAL SETUP ---
# Replace with your actual key from Google AI Studio
# Ensure there are no spaces before or after the key
API_KEY = "AIzaSyDmxYcafp5zoZ00CGLSatuT6JALfllSqQ4" 

genai.configure(api_key=API_KEY)

# Model
model = genai.GenerativeModel('gemini-pro')

# Page Configuration
st.set_page_config(page_title="SmartPort AI Assistant", page_icon="🚢")
st.title("🚢 SmartPort AI: Harbor Assistant")
st.markdown("Real-time risk management and port operations support.")

# --- 2. CHAT HISTORY (MEMORY) ---
# Initialize session state for chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your SmartPort assistant. How can I help with vessel risk assessment today?"}
    ]

# Display previous chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 3. INTERACTION LOGIC ---
if prompt := st.chat_input("Type your query about vessels or risks..."):
    
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response from Gemini
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # Generate the content based on the user prompt
            response = model.generate_content(prompt)
            full_response = response.text
            
            # Display assistant response
            message_placeholder.markdown(full_response)
            
            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            # Handle API errors (like the 400 error we discussed)
            error_msg = f"Connectivity Error: {str(e)}"
            st.error(error_msg)
            st.info("Tip: Double-check your API Key and ensure the 'Generative Language API' is enabled in your Google Cloud Project.")