"""Chunker and Metadata Tagger for Mutual Fund facts."""
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DocumentChunker:
    def __init__(self, processed_dir, output_dir):
        self.processed_dir = processed_dir
        self.output_dir = output_dir
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def chunk_text(self, text):
        """Split the processed text into individual sentence chunks."""
        # The sentences were joined by spaces and ended with periods.
        chunks = [chunk.strip() + "." for chunk in text.split(". ") if chunk.strip()]
        # Remove any trailing double dots if they happen
        chunks = [c.replace("..", ".") for c in chunks]
        return chunks

    def process_and_tag(self):
        """Read processed JSONs, chunk the text, and attach metadata."""
        all_chunks = []
        
        for filename in os.listdir(self.processed_dir):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(self.processed_dir, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            text = data.get("processed_text", "")
            if not text:
                continue
                
            fund_name = data.get("fund_name", "")
            fund_slug = data.get("fund_slug", filename.replace(".json", ""))
            url = data.get("url", "")
            last_updated = data.get("last_updated", "")

            chunks = self.chunk_text(text)

            for chunk in chunks:
                chunk_obj = {
                    "text": chunk,
                    "metadata": {
                        "fund_name": fund_name,
                        "fund_slug": fund_slug,
                        "source_url": url,
                        "last_updated": last_updated,
                    },
                }
                all_chunks.append(chunk_obj)
                
            logging.info(f"Created {len(chunks)} chunks for {fund_name}")
            
        # Save all tagged chunks into a single JSON file ready for embedding
        output_file = os.path.join(self.output_dir, "all_tagged_chunks.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=4)
            
        logging.info(f"Successfully saved {len(all_chunks)} total chunks to {output_file}")
        return all_chunks

if __name__ == "__main__":
    chunker = DocumentChunker("data/processed", "data/chunks")
    chunker.process_and_tag()
