import streamlit as st
import requests

st.set_page_config(page_title="Smart Hospital Network Agent", page_icon="🏥")

st.title("🏥 Smart Hospital Network Agent")
st.markdown("""
**Your AI Patient Financial Advocate & Provider Navigator**

This agent uses **Google Spanner Graph RAG** and real-time **CMS/NPPES API joins** to help you find in-network doctors. It is strictly mandated to educate patients on their financial responsibilities based on a doctor's **Medicare Assignment** status.

*Try asking:*
* *"Find an eye doctor in Saint Augustine, FL."*
* *"I need a Family Medicine doctor in Miami."*
""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("trace"):
            with st.expander("🔍 View Retrieval Trace (System Architecture)", expanded=False):
                st.code(message["trace"], language="yaml")

# React to user input
if prompt := st.chat_input("e.g. Which clinics is Dr. Provider 1 affiliated with?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Agent is thinking..."):
        try:
            # Get configuration from secrets, with a local fallback
            backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000/chat")
            api_key = st.secrets.get("API_KEY", "default-dev-key")
            
            response = requests.post(
                backend_url,
                json={"message": prompt},
                headers={"X-API-Key": api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse response based on ADK's return payload
            raw_reply = data.get("reply") or data.get("response") or str(data)
            
            # Split the reply from the trace if it exists
            if "---" in raw_reply and "**Retrieval Trace:**" in raw_reply:
                parts = raw_reply.split("\n\n---\n**Retrieval Trace:**\n")
                reply = parts[0]
                trace = parts[1] if len(parts) > 1 else ""
            else:
                reply = raw_reply
                trace = ""
            
        except Exception as e:
            reply = f"Error communicating with backend: {e}"
            trace = ""

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(reply)
        
        # Display the Retrieval Trace as a clean expander or info box
        if trace:
            with st.expander("🔍 View Retrieval Trace (System Architecture)", expanded=False):
                st.code(trace, language="yaml")
                
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": reply, "trace": trace})
