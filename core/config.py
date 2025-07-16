# core/config.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import ssl
from openai import OpenAI
from pythonjsonlogger.json import JsonFormatter

class Config:
    def __init__(self):
        env_path = Path(__file__).resolve().parents[1] / ".env"
        load_dotenv(dotenv_path=env_path)

        # self.self_host_llm = os.getenv("SELF_HOST_LLM", "false").lower() == "true"
        self.inference_api_url = os.getenv("INFERENCE_API_URL")
        self.inference_api_key = os.getenv("INFERENCE_API_KEY")
        self.inference_model_name = os.getenv("INFERENCE_MODEL_NAME")

        self.es_host = os.getenv("ES_HOST")
        self.es_user = os.getenv("ES_USER")
        self.es_password = os.getenv("ES_PASSWORD")
        self.es_index = os.getenv("ES_INDEX")

        self.embedding_model = os.getenv("EMBEDDING_MODEL")

        # Initialize clients
        self._es_client = None
        self._openai_client = None
        self._setup_logging()


    @property
    def es_client(self):
        """
        Initialize the ElasticSearch client. We're ditching security in this simple project, but you should never
        run like this in the real world.
        :return:
        """
        if self._es_client is None:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            self._es_client = Elasticsearch(
                self.es_host,
                basic_auth=(self.es_user, self.es_password),
                verify_certs=False,
                ssl_context=ssl_context
            )
        return self._es_client

    @property
    def openai_client(self):
        """
        This produces a client that works with any OpenAI compatible API (such as Ollama). You can swap to ChatGPT
        if you have an account and enjoy the giant context window. This would let you return more results from ES
        without sacrificing the rest of the system prompt, for example.
        :return:
        """
        if self._openai_client is None:
            base_url = self.inference_api_url.rstrip("/") + "/v1"
            self._openai_client = OpenAI(
                base_url=base_url,
                api_key=self.inference_api_key
            )
        return self._openai_client


    def _setup_logging(self):
        logger = logging.getLogger()
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = JsonFormatter("{message}{asctime}{exc_info}", style="{")
            handler.setFormatter(formatter)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)



