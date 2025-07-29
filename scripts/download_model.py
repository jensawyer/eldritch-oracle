import os
import sys
from pathlib import Path
import requests
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

MODEL_PATH = Path(os.getenv("LLM_MODEL_DIR"), os.getenv("LLM_MODEL_FILE"))
MODEL_URL = os.getenv("LLM_MODEL_URL")
HF_TOKEN = os.environ.get("HUGGINGFACE_TOKEN")

MIN_EXPECTED_SIZE = 1_000_000_000  # 1GB minimum expected model file size


def download_model():
    if not HF_TOKEN:
        print("HUGGINGFACE_TOKEN not found in .env. Please add it.")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    if MODEL_PATH.exists():
        file_size = MODEL_PATH.stat().st_size
        if file_size < MIN_EXPECTED_SIZE:
            print(
                f"⚠️ Model found at {MODEL_PATH}, but it's too small ({file_size} bytes). Redownloading..."
            )
            MODEL_PATH.unlink()
        else:
            print(f"Model already exists at {MODEL_PATH} ({file_size} bytes)")
            return

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"⬇️ Downloading model from {MODEL_URL} to {MODEL_PATH}...")

    try:
        response = requests.get(
            MODEL_URL, headers=headers, stream=True, allow_redirects=True, timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to download model: {e}")
        sys.exit(1)

    total = int(response.headers.get("content-length", 0))
    if total < MIN_EXPECTED_SIZE:
        print(
            f"Content length too small ({total} bytes). This may indicate a bad URL or an authentication issue."
        )
        sys.exit(1)

    with (
        open(MODEL_PATH, "wb") as f,
        tqdm(total=total, unit="B", unit_scale=True) as pbar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

    print("Download complete.")

    final_size = MODEL_PATH.stat().st_size
    if final_size < MIN_EXPECTED_SIZE:
        print(
            f"Final model size too small ({final_size} bytes). Deleting corrupt file."
        )
        MODEL_PATH.unlink(missing_ok=True)
        sys.exit(1)


if __name__ == "__main__":
    download_model()
