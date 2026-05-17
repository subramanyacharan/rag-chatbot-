"""Phase 3.1 and 3.2: Query Processing and Semantic Retrieval."""
import logging
import os

import chromadb

from src.phase2_knowledge_base.fund_registry import detect_fund_slug, fund_from_slug
from src.phase2_knowledge_base.vector_db import ensure_vector_db_populated
from src.phase3_rag_engine.embeddings import get_embedding_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

RELEVANCE_MAX_DISTANCE = float(os.environ.get("RELEVANCE_MAX_DISTANCE", "1.15"))


class FactRetriever:
    def __init__(
        self,
        db_dir=None,
        collection_name="mutual_fund_facts",
        chunks_file=None,
    ):
        self.db_dir = db_dir or os.environ.get("CHROMA_DB_DIR", "data/chroma_db")
        self.collection_name = collection_name
        self.chunks_file = chunks_file or os.environ.get(
            "CHUNKS_FILE", "data/chunks/all_tagged_chunks.json"
        )

        ensure_vector_db_populated(
            chunks_file=self.chunks_file,
            db_dir=self.db_dir,
            collection_name=self.collection_name,
        )

        self.model = get_embedding_model()
        logging.info("Connecting to ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path=self.db_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )

    def retrieve_context(self, query: str, top_k: int = 5):
        """Embed the query and retrieve the most relevant chunks."""
        logging.info("Processing query: '%s'", query)
        fund_slug = detect_fund_slug(query)

        emb = self.model.encode([query])
        query_embedding = emb.tolist() if hasattr(emb, "tolist") else emb

        query_kwargs = {
            "query_embeddings": query_embedding,
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if fund_slug:
            query_kwargs["where"] = {"fund_slug": fund_slug}
            logging.info("Filtering retrieval to fund_slug=%s", fund_slug)

        results = self.collection.query(**query_kwargs)
        formatted = self._format_results(results)

        if fund_slug and not formatted:
            logging.info("No chunks for slug filter; retrying without filter.")
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            formatted = self._format_results(results)
            formatted = self._prefer_slug(formatted, fund_slug)

        if not fund_slug:
            formatted = self._dedupe_by_fund(formatted)

        return [c for c in formatted if c.get("distance", 999) <= RELEVANCE_MAX_DISTANCE][
            :top_k
        ] or formatted[:top_k]

    def _prefer_slug(self, chunks: list, fund_slug: str) -> list:
        matched = [c for c in chunks if c["metadata"].get("fund_slug") == fund_slug]
        other = [c for c in chunks if c["metadata"].get("fund_slug") != fund_slug]
        return matched + other

    def _dedupe_by_fund(self, chunks: list) -> list:
        seen = set()
        out = []
        for c in chunks:
            slug = c["metadata"].get("fund_slug", "")
            if slug in seen:
                continue
            seen.add(slug)
            out.append(c)
        return out + [c for c in chunks if c not in out]

    def _format_results(self, raw_results):
        formatted = []
        if not raw_results or not raw_results.get("documents") or not raw_results["documents"][0]:
            return formatted

        docs = raw_results["documents"][0]
        metadatas = raw_results["metadatas"][0]
        distances = raw_results["distances"][0]

        for i in range(len(docs)):
            formatted.append(
                {
                    "text": docs[i],
                    "metadata": metadatas[i],
                    "distance": distances[i],
                }
            )
        return formatted


def pick_source_chunk(query: str, chunks: list) -> dict | None:
    """Choose metadata for citation from the chunk that best matches the query fund."""
    if not chunks:
        return None
    fund_slug = detect_fund_slug(query)
    if fund_slug:
        for chunk in chunks:
            if chunk["metadata"].get("fund_slug") == fund_slug:
                return chunk
    return chunks[0]
