import os

# Prevent Hugging Face warning about unsafe use of `tokenizers` with multiprocessing.
# This avoids logs like:
# "The current process just got forked, after parallelism has already been used..."
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from core.config import Config
from services.chat_service import RAGAgent
from services.search_service import ESSearch

logger = logging.getLogger(__name__)


class AppState:
    agent: RAGAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config()
    search = ESSearch(config)
    logger.info("Initializing RAGAgent")
    agent = RAGAgent(config, search)
    app.state = AppState
    app.state.agent = agent
    yield
    logger.info("Shutting down RAGAgent...")


app = FastAPI(lifespan=lifespan)


# Optional CORS: gate by explicit allowlist via env var
# Example: CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
allowed_origins = [
    o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o.strip()
]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
    )

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Eldritch Oracle RAG API is running"}
