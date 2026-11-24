import os
import sys

# app root (parent of controllers/) so `core` and `models` import from any cwd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI

from core.agent import chat
from models.schema import ChatRequest, ChatResponse, HealthResponse

app = FastAPI(title="Info Buddy")


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version="v2")


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    # plain def: FastAPI runs it in a threadpool, so the blocking LLM call doesn't stall the server
    return ChatResponse(reply=chat(req.message))
