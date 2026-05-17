"""Vector Database Manager for generating embeddings and upserting chunks."""
import os
import json
import logging
import uuid
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class VectorDBManager:
    def __init__(self, chunks_file, db_dir, collection_name="mutual_fund_facts"):
        self.chunks_file = chunks_file
        self.db_dir = db_dir
        self.collection_name = collection_name
        
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            
        logging.info("Initializing SentenceTransformer (BAAI/bge-small-en-v1.5)...")
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        
        logging.info(f"Initializing ChromaDB at {self.db_dir}...")
        self.chroma_client = chromadb.PersistentClient(path=self.db_dir)
        self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)

    def load_chunks(self):
        """Load tagged chunks from JSON."""
        if not os.path.exists(self.chunks_file):
            logging.error(f"Chunks file not found: {self.chunks_file}")
            return []
            
        with open(self.chunks_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def process_and_store(self):
        """Generate embeddings and store chunks in ChromaDB."""
        chunks = self.load_chunks()
        if not chunks:
            return
            
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Generate unique IDs for each chunk
        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
        
        logging.info(f"Generating embeddings for {len(texts)} chunks...")
        emb = self.model.encode(texts)
        embeddings = emb.tolist() if hasattr(emb, 'tolist') else emb
        
        logging.info("Upserting into ChromaDB collection...")
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )
        logging.info("Vector database successfully populated.")

    def search(self, query, top_k=3):
        """Utility method to test retrieval."""
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        return results

if __name__ == "__main__":
    db_manager = VectorDBManager(
        chunks_file="data/chunks/all_tagged_chunks.json",
        db_dir="data/chroma_db"
    )
    db_manager.process_and_store()
