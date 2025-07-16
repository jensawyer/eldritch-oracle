from fastapi import APIRouter, Depends, Request, HTTPException
from models.chat import ChatRequest, ChatMessage
from services.chat_service import RAGAgent

router = APIRouter()

def get_agent(request: Request):
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="RAGAgent not initialized")
    return agent

@router.post("/chat")
async def chat(request: ChatRequest, agent = Depends(get_agent), response_model=ChatMessage):
    return agent.generate_response(request)

# def router(agent: RAGAgent) -> APIRouter:
#     router = APIRouter()
#
#     @router.post("/chat", response_model=ChatMessage)
#     def chat(request: ChatRequest):
#         return agent.generate_response(request)
#
#     @router.get("/health")
#     def health_check():
#         return {"status": "ok"}
#
#     return router



