import os
from typing import Tuple
from transformers import pipeline

# default summariser model
MODEL_NAME = os.getenv("SR_SUMM_MODEL", "sshleifer/distilbart-cnn-12-6")

# initialise pipeline once (don’t reload on every call)
_summariser = pipeline(
    "summarization",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    framework="pt",
    truncation=True
)

def abstractive_summarize(text: str, target: str = "medium") -> Tuple[str, int]:
    """
    Perform chunked abstractive summarization using a pre-trained transformer.
    target = 'short' | 'medium' | 'long' controls compression strength.
    """
    text = text.strip()
    if not text:
        return "", 0

    # chunk size and target summary length presets
    if target == "short":
        chunk_size, summary_len = 700, 130
    elif target == "long":
        chunk_size, summary_len = 1200, 250
    else:
        chunk_size, summary_len = 900, 180

    # break text into overlapping-ish chunks
    words = text.split()
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

    results = []
    for ch in chunks:
        out = _summariser(ch, max_length=summary_len, min_length=50, do_sample=False)
        results.append(out[0]["summary_text"].strip())

    # optional “summary of summaries” if it’s long
    joined = " ".join(results)
    if len(results) > 2:
        final = _summariser(joined, max_length=summary_len, min_length=50, do_sample=False)
        joined = final[0]["summary_text"].strip()

    return joined, len(chunks)
