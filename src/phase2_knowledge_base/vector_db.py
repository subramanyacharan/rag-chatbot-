"""Vector Database Manager for generating embeddings and upserting chunks."""
import hashlib
import json
import logging
import os

import chromadb

from src.phase3_rag_engine.embeddings import get_embedding_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_CHUNKS_FILE = "data/chunks/all_tagged_chunks.json"
DEFAULT_DB_DIR = "data/chroma_db"
DEFAULT_COLLECTION_NAME = "mutual_fund_facts"


def _chunks_fingerprint(chunks_file: str) -> str:
    with open(chunks_file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _fingerprint_path(db_dir: str) -> str:
    return os.path.join(db_dir, ".chunks_fingerprint")


def _read_stored_fingerprint(db_dir: str) -> str | None:
    path = _fingerprint_path(db_dir)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    return None


def _write_fingerprint(db_dir: str, fingerprint: str) -> None:
    os.makedirs(db_dir, exist_ok=True)
    with open(_fingerprint_path(db_dir), "w", encoding="utf-8") as f:
        f.write(fingerprint)


def ensure_vector_db_populated(
    chunks_file=DEFAULT_CHUNKS_FILE,
    db_dir=DEFAULT_DB_DIR,
    collection_name=DEFAULT_COLLECTION_NAME,
):
    """Create or refresh the Chroma collection when empty or chunks changed."""
    if not os.path.exists(chunks_file):
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        client = chromadb.PersistentClient(path=db_dir)
        if client.get_or_create_collection(name=collection_name).count() > 0:
            logging.info("ChromaDB collection '%s' ready (cached).", collection_name)
            return
        raise FileNotFoundError(
            f"Chroma collection '{collection_name}' is empty and chunks file not found: {chunks_file}"
        )

    fingerprint = _chunks_fingerprint(chunks_file)
    stored = _read_stored_fingerprint(db_dir)

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    client = chromadb.PersistentClient(path=db_dir)
    collection = client.get_or_create_collection(name=collection_name)
    expected = len(json.load(open(chunks_file, encoding="utf-8")))

    if (
        collection.count() == expected
        and collection.count() > 0
        and stored == fingerprint
    ):
        logging.info(
            "ChromaDB collection '%s' ready (%d documents).",
            collection_name,
            collection.count(),
        )
        return

    logging.info(
        "Refreshing ChromaDB '%s' (%d docs expected, had %d).",
        collection_name,
        expected,
        collection.count(),
    )
    manager = VectorDBManager(chunks_file, db_dir, collection_name)
    manager.process_and_store()
    _write_fingerprint(db_dir, fingerprint)


class VectorDBManager:
    def __init__(self, chunks_file, db_dir, collection_name="mutual_fund_facts"):
        self.chunks_file = chunks_file
        self.db_dir = db_dir
        self.collection_name = collection_name

        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)

        self.model = get_embedding_model()
        self.chroma_client = chromadb.PersistentClient(path=self.db_dir)
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
        except (ValueError, Exception):
            pass
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )

    def load_chunks(self):
        if not os.path.exists(self.chunks_file):
            logging.error("Chunks file not found: %s", self.chunks_file)
            return []

        with open(self.chunks_file, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _chunk_id(chunk: dict) -> str:
        meta = chunk.get("metadata", {})
        slug = meta.get("fund_slug", "unknown")
        text_hash = hashlib.md5(chunk["text"].encode("utf-8")).hexdigest()[:12]
        return f"{slug}:{text_hash}"

    def process_and_store(self):
        chunks = self.load_chunks()
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [self._chunk_id(chunk) for chunk in chunks]

        logging.info("Generating embeddings for %d chunks...", len(texts))
        emb = self.model.encode(texts, batch_size=32, show_progress_bar=False)
        embeddings = emb.tolist() if hasattr(emb, "tolist") else emb

        logging.info("Upserting into ChromaDB collection...")
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts,
        )
        logging.info("Vector database populated with %d documents.", len(ids))


if __name__ == "__main__":
    db_manager = VectorDBManager(
        chunks_file="data/chunks/all_tagged_chunks.json",
        db_dir="data/chroma_db",
    )
    db_manager.process_and_store()
    _write_fingerprint("data/chroma_db", _chunks_fingerprint(DEFAULT_CHUNKS_FILE))
