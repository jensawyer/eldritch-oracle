from elasticsearch import Elasticsearch
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

ES_HOST = os.getenv("ES_HOST")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_PASSWORD")
ES_INDEX = os.getenv("ES_INDEX")

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False,     # don't do this in production environments
    request_timeout=10,
)

try:
    info = es.info()
    print("Connected to Elasticsearch")
    print(f"Cluster: {info['cluster_name']} | Version: {info['version']['number']}")
except Exception as e:
    print(f"Could not connect to Elasticsearch:\n{type(e).__name__}: {e}")
    sys.exit(1)

# Check if index exists
if not es.indices.exists(index=ES_INDEX):
    print(f"Index '{ES_INDEX}' does not exist.")
    sys.exit(2)

print(f"Index '{ES_INDEX}' exists.")

# Count documents
try:
    count = es.count(index=ES_INDEX)['count']
    if count == 0:
        print(f"Index '{ES_INDEX}' exists but contains 0 documents.")
        sys.exit(3)
    else:
        print(f"Index contains {count} documents.")
except Exception as e:
    print(f"Error counting documents:\n{type(e).__name__}: {e}")
    sys.exit(4)

