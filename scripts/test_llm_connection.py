# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "dotenv>=0.9.9",
#   "openai>=1.86.0",
# ]
# ///

import os
import sys
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

INFERENCE_API_URL = os.getenv("INFERENCE_API_URL")
INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY")
INFERENCE_MODEL_NAME = os.getenv("INFERENCE_MODEL_NAME")
BASE_URL = INFERENCE_API_URL.rstrip("/") + "/v1"

print(f"Python exec: {sys.executable}")
print(f"Version: {sys.version}")

try:
    openai_client = OpenAI(base_url=BASE_URL, api_key=INFERENCE_API_KEY)
    models = openai_client.models.list()
    print(f"LLM is reachable. Found {len(models.data)} model(s).")
    model_ids = {m.id for m in models.data}
    if INFERENCE_MODEL_NAME in model_ids:
        print(f"Model '{INFERENCE_MODEL_NAME}' is available on the inference server.")
    else:
        print(f"ERROR: Model '{INFERENCE_MODEL_NAME}' not found on the server.")
        print(f"Available models: {', '.join(model_ids) or '[none]'}")
        sys.exit(1)


except Exception as e:
    print(f"ERROR: Failed to connect to LLM inference server: {e}")
    sys.exit(1)
