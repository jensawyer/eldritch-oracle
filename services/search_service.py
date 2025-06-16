from typing import List, Dict
from models.chat import ChatMessage
from core.config import Config
import logging
from sentence_transformers import SentenceTransformer

class ESSearch:

    def __init__(self, config:Config):
        self.es_client = config.es_client
        self.index = config.es_index
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.addHandler(config.loghandler_config)
        self.encoder = SentenceTransformer(config.embedding_model)

    def embed_query(self, query:str) -> list[int]:
        return self.encoder.encode(query, normalize_embeddings=True).tolist()

    def search(self, messages: list[ChatMessage], top_k=5) -> list[dict]:
        latest_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        if not latest_user_msg:
            return []
        embedding = self.embed_query(latest_user_msg)
        body = {
            "size": top_k,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": embedding}
                    }
                }
            }
        }
        result = self.es_client.search(index=self.index, body=body)
        return result


# def retrieve_relevant_chunks(messages: List[ChatMessage]) -> List[Dict]:
#     """
#     Stub for retrieving relevant chunks from ElasticSearch using the latest user query.
#     """
#     latest_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
#     if not latest_user_msg:
#         return []
#
#     # TODO: Hook into real ElasticSearch client and return top-k matches
#     return [{"content": "Necronomicon is a fictional grimoire..."}]
