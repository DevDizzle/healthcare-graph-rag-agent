from agent.network_agent import agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps import App
import asyncio

async def test():
    app = App(name="test_app", agent=agent)
    runner = Runner(app=app, session_service=InMemorySessionService())
    response = await runner.run_async(session_id="test_session", user_message="hello")
    async for event in response:
        print(event)

asyncio.run(test())
