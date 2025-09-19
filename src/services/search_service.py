from models.chat import ChatMessage
from core.config import Config
import logging


class ESSearch:
    def __init__(self, config: Config):
        self.es_client = config.es_client
        self.index: str = config.es_index
        self.embedding_model: str = config.embedding_model
        self.top_k_results: str = config.top_k_search_results
        self.logger = logging.getLogger(self.__class__.__name__)
        self._encoder = None

    @property
    def encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer

            self._encoder = SentenceTransformer(self.embedding_model)
        return self._encoder

    def embed_query(self, query: str) -> list[int]:
        return self.encoder.encode(query, normalize_embeddings=True).tolist()

    def search(self, messages: list[ChatMessage], top_k) -> list[str]:
        """
        This version of search is just doing simple vector similarity. It's not great for negation or any
        sort of deeper linguistic preprocessing that could enhance results, but it is a simple for a personal project
        and sufficient for now.
        :param messages: The list of messages coming in for lookup. Better not be very many if the LLM context window is small!
        :param top_k: The number of best results to return. Keep this value small for a small window! The number of results
        before things break is related to the sum of the size of the context window, length of the rest of the system prompt, length of the
        chunks of text as you preprocessed with the prep_docs script, and whether you are feeding context back in for future turns (we aren't for now)
        :return: The list of document strings
        """
        latest_user_msg = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        if not latest_user_msg:
            return []
        embedding = self.embed_query(latest_user_msg)
        body = {
            "size": self.top_k_results,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": embedding},
                    },
                }
            },
        }
        search_result = self.es_client.search(index=self.index, body=body)
        result = []
        for hit in search_result["hits"]["hits"]:
            del hit["_source"]["embedding"]
            result.append(str(hit["_source"]))
        self.logger.debug(result)
        return result
