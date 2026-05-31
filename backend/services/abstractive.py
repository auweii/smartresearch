import os
import torch
from typing import Tuple
from transformers import pipeline

MODEL_NAME = os.getenv("SR_SUMM_MODEL", "sshleifer/distilbart-cnn-12-6")

_summariser = None


def _get_summariser():
    global _summariser
    if _summariser is None:
        device = 0 if torch.cuda.is_available() else -1
        _summariser = pipeline(
            "summarization",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            framework="pt",
            truncation=True,
            device=device,
        )
        print(f"✅ Summariser loaded on {'GPU' if device == 0 else 'CPU'}")
    return _summariser


def abstractive_summarize(text: str, target: str = "medium") -> Tuple[str, int]:
    text = text.strip()
    if not text:
        return "", 0

    if target == "short":
        chunk_size, summary_len, min_len = 600, 200, 100
    elif target == "long":
        chunk_size, summary_len, min_len = 1400, 1024, 400
    else:
        chunk_size, summary_len, min_len = 900, 512, 200

    words = text.split()
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    summariser = _get_summariser()

    results = []
    for ch in chunks:
        out = summariser(ch, max_length=summary_len, min_length=min_len, do_sample=False)
        results.append(out[0]["summary_text"].strip())

    joined = " ".join(results)
    # merge chunk summaries if there are many
    if len(results) > 2:
        final = summariser(joined, max_length=summary_len, min_length=min_len, do_sample=False)
        joined = final[0]["summary_text"].strip()

    return joined, len(chunks)