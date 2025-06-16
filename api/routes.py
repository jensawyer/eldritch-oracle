from fastapi import APIRouter
from models.chat import ChatRequest, ChatMessage
from services.chat_service import RAGAgent


def router(agent: RAGAgent) -> APIRouter:
    router = APIRouter()

    @router.post("/chat", response_model=ChatMessage)
    def chat(request: ChatRequest):
        return agent.generate_response(request)

    @router.get("/health")
    def health_check():
        return {"status": "ok"}

    return router



