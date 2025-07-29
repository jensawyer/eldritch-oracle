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


# CORS setup if you want to use this from a browser frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Eldritch Oracle RAG API is running"}
