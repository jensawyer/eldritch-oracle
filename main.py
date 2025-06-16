from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from dotenv import load_dotenv
from core.config import Config
from services.chat_service import RAGAgent
from services.search_service import ESSearch



config = Config()
search = ESSearch(config)
rag_agent = RAGAgent(config, search)

app = FastAPI()

# CORS setup if you want to use this from a browser frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router(rag_agent), prefix='/api')

@app.get("/")
def root():
    return {"message": "Eldritch Oracle RAG API is running"}