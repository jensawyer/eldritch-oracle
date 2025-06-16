from core.config import Config

class VectorStore:
    def __init__(self, config: Config):
        self.es = config.es
        self.index = config.es_index

    def add_documents(self, docs: list[dict]) -> None:
        # assume docs have embedding + metadata
        actions = [
            {"_op_type": "index", "_index": self.index, "_source": doc}
            for doc in docs
        ]
        helpers.bulk(self.es, actions)

    def delete_by_id(self, doc_id: str) -> None:
        self.es.delete(index=self.index, id=doc_id, ignore=[404])

    def search(self, embedding: list[float], top_k: int = 5) -> list[dict]:
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
        res = self.es.search(index=self.index, body=body)
        return [hit["_source"] for hit in res["hits"]["hits"]]
