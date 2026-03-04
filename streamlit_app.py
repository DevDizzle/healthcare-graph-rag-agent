import streamlit as st
import requests

st.set_page_config(page_title="Smart Hospital Network Agent", page_icon="🏥")

st.title("🏥 Smart Hospital Network Agent")
st.markdown("Ask me about providers, clinics, and hospitals.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("e.g. Which clinics is Dr. Provider 1 affiliated with?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Agent is thinking..."):
        try:
            # Assuming your ADK backend is running on port 8000 (e.g. via `adk web` or a custom FastAPI wrapper)
            response = requests.post(
                "http://localhost:8000/chat",
                json={"message": prompt}
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse response based on ADK's return payload
            reply = data.get("reply") or data.get("response") or str(data)
            
        except Exception as e:
            reply = f"Error communicating with backend: {e}"

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(reply)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": reply})
