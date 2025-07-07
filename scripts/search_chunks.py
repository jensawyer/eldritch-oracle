import os
import json
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import urllib3

# Disable TLS warning spam
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load env
load_dotenv()

ES_HOST = os.getenv("ES_HOST", "https://localhost:30920")
ES_INDEX = os.getenv("ES_INDEX", "lovecraft_chunks")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASS = os.getenv("ES_PASSWORD", "changeme")
MODEL_NAME = "BAAI/bge-base-en-v1.5"

# Connect to Elasticsearch
es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False
)

# Load encoder
encoder = SentenceTransformer(MODEL_NAME)

def embed_query(query: str):
    return encoder.encode(query, normalize_embeddings=True).tolist()

def search(query: str, top_k=5):
    print(f"\n🔍 Searching for: {query}")
    embedding = embed_query(query)

    body = {
        "size": top_k,
        "query": {
            "script_score": {
                "query": { "match_all": {} },
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": { "query_vector": embedding }
                }
            }
        }
    }

    res = es.search(index=ES_INDEX, body=body)

    for i, hit in enumerate(res["hits"]["hits"]):
        score = hit["_score"]
        source = hit["_source"]
        print(f"\n#{i+1} — Score: {score:.3f}")
        print(f"[{source['story_title']}] — {source['text']}")

if __name__ == "__main__":
    print("Ask the DB for chunks directly to see the raw outputs most close to your query.")
    while True:
        try:

            query = input("\n🐙 Ask the Eldrich Oracle (or 'exit'): ").strip()
            if query.lower() in ("exit", "quit"):
                break
            search(query)
        except KeyboardInterrupt:
            break
