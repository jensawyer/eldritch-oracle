import os
from pathlib import Path
import requests
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = Path(os.getenv("LLM_MODEL_PATH", "../models/llama3/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"))
MODEL_URL = "https://huggingface.co/TheBloke/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"

def download_model():
    if MODEL_PATH.exists():
        print(f"✅ Model already exists at {MODEL_PATH}")
        return

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"⬇️ Downloading model to {MODEL_PATH}...")

    response = requests.get(MODEL_URL, stream=True)
    total = int(response.headers.get('content-length', 0))
    with open(MODEL_PATH, 'wb') as f, tqdm(total=total, unit='B', unit_scale=True) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

    print("✅ Download complete.")

if __name__ == "__main__":
    download_model()
