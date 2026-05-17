"""Phase 3.1 and 3.2: Query Processing and Semantic Retrieval."""
import os
import chromadb
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FactRetriever:
    def __init__(self, db_dir="data/chroma_db", collection_name="mutual_fund_facts"):
        self.db_dir = db_dir
        self.collection_name = collection_name
        
        logging.info("Loading embedding model (BAAI/bge-small-en-v1.5)...")
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        
        logging.info("Connecting to ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path=self.db_dir)
        self.collection = self.chroma_client.get_collection(name=self.collection_name)

    def retrieve_context(self, query: str, top_k: int = 3):
        """
        Phase 3.1: Embed the user's query.
        Phase 3.2: Retrieve the top-K relevant chunks from ChromaDB.
        """
        logging.info(f"Processing query: '{query}'")
        # 3.1 Query Processing
        emb = self.model.encode([query])
        query_embedding = emb.tolist() if hasattr(emb, 'tolist') else emb
        
        # 3.2 Semantic Retrieval
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        return self._format_results(results)
        
    def _format_results(self, raw_results):
        """Format the ChromaDB raw results into a cleaner list of dictionaries."""
        formatted = []
        if not raw_results or not raw_results.get('documents') or not raw_results['documents'][0]:
            return formatted
            
        docs = raw_results['documents'][0]
        metadatas = raw_results['metadatas'][0]
        distances = raw_results['distances'][0]
        
        for i in range(len(docs)):
            formatted.append({
                "text": docs[i],
                "metadata": metadatas[i],
                "distance": distances[i]
            })
            
        return formatted

if __name__ == "__main__":
    retriever = FactRetriever()
    
    # Test query
    sample_query = "What is the expense ratio of HDFC Mid-Cap Fund?"
    results = retriever.retrieve_context(sample_query)
    
    print(f"\n--- Results for: '{sample_query}' ---")
    for idx, res in enumerate(results, 1):
        print(f"\nResult {idx} (Distance: {res['distance']:.4f}):")
        print(f"Text: {res['text']}")
        print(f"Source URL: {res['metadata']['source_url']}")
        print(f"Last Updated: {res['metadata']['last_updated']}")
