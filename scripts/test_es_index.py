from elasticsearch import Elasticsearch
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import ssl
import warnings
from urllib3.exceptions import InsecureRequestWarning
import logging

logger = logging.getLogger(__name__)

# We're filtering this warning because we're running ElasticSearch in an insecure local dev mode. Without this
# we end up getting a swarm of warnings that aren't helping in this case.
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
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
    verify_certs=False,     # don't do this in production environments
    ssl_context=context)

# Check if index exists
if not es.indices.exists(index=ES_INDEX):
    logger.info(f"Index '{ES_INDEX}' does not exist.")
    sys.exit(2)

logger.info(f"Index '{ES_INDEX}' exists.")

# Count documents
try:
    with open(CORPUS_JSONL_FILE, 'r') as file:
        lines = file.readlines()
        num_lines = len(lines)
        logger.info(f"The file has {num_lines} lines.")
        count = es.count(index=ES_INDEX)['count']
        if count == 0:
            logger.error(f"Index '{ES_INDEX}' exists but contains 0 documents. You need to run the index command.")
            sys.exit(3)
        elif count == num_lines:
            logger.error(f"Index and jsonl file contain {count} entries. Looks like everything is indexed!")
        else:
            logger.error(f"Index contains {count} documents and we expected {num_lines} from the corpus jsonl file. You should "
                  f"reindex or just know you might not get expected results.")
            sys.exit(4)
except Exception as e:
    logger.error(f"Error counting documents:\n{type(e).__name__}: {e}")
    sys.exit(4)
