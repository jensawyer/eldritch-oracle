from elasticsearch import Elasticsearch
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import ssl
import warnings
from urllib3.exceptions import InsecureRequestWarning
import logging

# We're filtering this warning because we're running ElasticSearch in an insecure local dev mode. Without this
# we end up getting a swarm of warnings that aren't helping in this case.
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

logger = logging.getLogger(__name__)


env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# Create a secure context that ignores certificate verification (for local dev)
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

ES_HOST = os.getenv("ES_HOST")
ES_USER = os.getenv("ES_USER")
ES_PASS = os.getenv("ES_PASSWORD")
ES_INDEX = os.getenv("ES_INDEX")
CORPUS_JSONL_FILE = os.getenv("CORPUS_JSONL_FILE")

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False,  # don't do this in production environments
    ssl_context=context,
)

try:
    info = es.info()
    logger.info("Connected to Elasticsearch")
    logger.info(
        f"Cluster: {info['cluster_name']} | Version: {info['version']['number']}"
    )
except Exception as e:
    logger.error(f"Could not connect to Elasticsearch:\n{type(e).__name__}: {e}")
    sys.exit(1)
