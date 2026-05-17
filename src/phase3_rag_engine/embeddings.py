"""Shared embedding model (loaded once per process)."""
import logging
from sentence_transformers import SentenceTransformer

_model = None

MODEL_NAME = "BAAI/bge-small-en-v1.5"


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logging.info("Loading embedding model (%s)...", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model
