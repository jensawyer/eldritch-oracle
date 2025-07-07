import json
import os
from pathlib import Path
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
import ssl

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
# Create a secure context that ignores certificate verification (for local dev)
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

JSONL_PATH = os.getenv("CORPUS_JSONL_FILE")
ES_HOST = os.getenv("ES_HOST")
ES_INDEX = os.getenv("ES_INDEX")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_PASSWORD")

if not JSONL_PATH or not Path(JSONL_PATH).exists():
    raise FileNotFoundError(f"CORPUS_JSONL_FILE not found: {JSONL_PATH}")

# Set up Elasticsearch client
es = Elasticsearch(ES_HOST,
                   basic_auth=(ES_USER, ES_PASS),
                   verify_certs=False,
                   ssl_context=context)

# Create index if not exists
def create_index():
    if es.indices.exists(index=ES_INDEX):
        print(f"ℹ️ Index '{ES_INDEX}' already exists.")
        return

    print(f"Creating index '{ES_INDEX}'...")
    es.indices.create(index=ES_INDEX, body={
        "mappings": {
            "properties": {
                "story_title": { "type": "keyword" },
                "chunk_id":    { "type": "integer" },
                "text":        { "type": "text" },
                "source":      { "type": "keyword" },
                "start_token": { "type": "integer" },
                "end_token":   { "type": "integer" },
                "embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    })

# Generator for bulk indexing
def generate_docs():
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            yield {
                "_op_type": "index",
                "_index": ES_INDEX,
                "_source": doc
            }

def main():
    if not es.ping():
        raise ConnectionError("Failed to connect to Elasticsearch")

    create_index()

    print(f"Indexing chunks from {JSONL_PATH} into '{ES_INDEX}'...")
    result = helpers.bulk(es, generate_docs())
    print(f"Indexed {result[0]} documents successfully.")

if __name__ == "__main__":
    main()
