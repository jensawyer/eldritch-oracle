from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

load_dotenv()

ES_HOST = os.getenv("ES_HOST", "https://localhost:30920")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASS = os.getenv("ES_PASSWORD", "changeme")

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False,     # ← this disables SSL cert verification the *right* way
    request_timeout=10,
)

try:
    info = es.info()
    print("✅ Connected!")
    print(f"🧠 Cluster: {info['cluster_name']} | Version: {info['version']['number']}")
except Exception as e:
    print(f"❌ Final error:\n{type(e).__name__}: {e}")
