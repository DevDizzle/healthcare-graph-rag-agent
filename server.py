from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import asyncio
import os
import uuid
import traceback
from agent.network_agent import agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps import App
from google.genai.types import Content, Part

app = FastAPI(title="Smart Hospital Network Agent API")

API_KEY = os.environ.get("API_KEY", "default-dev-key")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Initialize ADK App and Session Service
adk_app = App(name="hospital_app", root_agent=agent)
session_svc = InMemorySessionService()

async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, api_key: str = Depends(get_api_key)):
    try:
        session_id = str(uuid.uuid4())
        await session_svc.create_session(app_name="hospital_app", user_id="user", session_id=session_id)
        runner = Runner(app=adk_app, session_service=session_svc)
        
        message = Content(role="user", parts=[Part.from_text(text=request.message)])
        response_generator = runner.run_async(user_id="user", session_id=session_id, new_message=message)
        
        full_text = ""
        tool_traces = []
        async for event in response_generator:
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if part.text:
                        full_text += part.text
                    if part.function_call:
                        tool_traces.append(f"Used tool: {part.function_call.name}")
                        if part.function_call.name == "search_nppes":
                             tool_traces.append("Real-Time Join: NPPES API -> CMS Medicare API")
                        elif part.function_call.name == "execute_gql":
                             tool_traces.append("Graph Search: Querying local Spanner Graph")
                        
        if not full_text:
            full_text = "Sorry, I could not generate a response."
            
        trace_str = "\n".join(tool_traces) if tool_traces else "No external tools used."
            
        return ChatResponse(reply=full_text + "\n\n---\n**Retrieval Trace:**\n" + trace_str)
    except Exception as e:
        print(f"Error during chat: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
