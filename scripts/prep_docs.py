import json
import os
from pathlib import Path
from typing import List, Dict
import spacy
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv
import re

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# Config
INPUT_FILE_DIR = os.getenv("CORPUS_RAW_FILE_DIR")
OUTPUT_FILE = os.getenv("CORPUS_JSONL_FILE")
SPACY_MODEL = os.getenv("SPACY_MODEL")
MAX_TOKENS = 400
OVERLAP = 50
MODEL = "BAAI/bge-base-en-v1.5"

# Load NLP and tokenizer

nlp = spacy.load(SPACY_MODEL)
encoder = SentenceTransformer(MODEL)
tokenizer = encoder.tokenizer

# Utility: extract title from first line
def extract_title(first_line: str) -> str:
    match = re.match(r'["“](.+?)["”]\s+by', first_line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Unknown Title"

def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))

def chunk_and_embed_story(text: str, title: str, source_file: str) -> List[Dict]:
    doc = nlp(text)
    chunks = []
    current_chunk = []
    current_tokens = 0
    start_token = 0

    def chunk_text():
        nonlocal start_token
        chunk_str = " ".join(current_chunk)
        end_token = start_token + current_tokens
        embedding = encoder.encode(chunk_str, normalize_embeddings=True).tolist()
        result = {
            "story_title": title,
            "text": chunk_str,
            "chunk_id": len(chunks),
            "source": source_file,
            "start_token": start_token,
            "end_token": end_token,
            "embedding": embedding
        }
        chunks.append(result)
        # Slide window for overlap
        if OVERLAP:
            overlap_sents = current_chunk[-OVERLAP:]
            start_token = end_token - sum(count_tokens(s) for s in overlap_sents)
            current_chunk[:] = overlap_sents
            return sum(count_tokens(s) for s in current_chunk)
        else:
            current_chunk.clear()
            start_token = end_token
            return 0

    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_tokens = count_tokens(sent_text)

        if current_tokens + sent_tokens > MAX_TOKENS and current_chunk:
            current_tokens = chunk_text()

        current_chunk.append(sent_text)
        current_tokens += sent_tokens

    # Final chunk
    if current_chunk:
        chunk_text()

    return chunks

def main():
    input_path = Path(INPUT_FILE_DIR)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for file_path in tqdm(list(input_path.glob("*.txt")), desc="Processing stories"):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    assert(f"There are no lines in the file: {file_path.name}")
                title_line = lines[0].strip()
                story_text = "".join(lines[1:]).strip()
                story_title = extract_title(title_line)

                story_chunks = chunk_and_embed_story(story_text, story_title, file_path.name)
                for chunk in story_chunks:
                    out_f.write(json.dumps(chunk) + "\n")

    print(f"Finished writing chunks to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
