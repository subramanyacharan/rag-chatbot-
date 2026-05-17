import os
import json
import pytest
from src.phase2_knowledge_base.chunker import DocumentChunker

@pytest.fixture
def chunker(tmp_path):
    processed_dir = tmp_path / "processed"
    chunks_dir = tmp_path / "chunks"
    processed_dir.mkdir()
    chunks_dir.mkdir()
    return DocumentChunker(str(processed_dir), str(chunks_dir))

def test_chunk_text(chunker):
    text = "The expense ratio is 0.5%. The NAV is 100. It is good."
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 3
    assert chunks[0] == "The expense ratio is 0.5%."
    assert chunks[1] == "The NAV is 100."
    assert chunks[2] == "It is good."

def test_process_and_tag(chunker):
    # Setup dummy processed data
    dummy_data = {
        "fund_name": "Test Fund",
        "url": "http://example.com",
        "last_updated": "2023-01-01",
        "processed_text": "Fact 1. Fact 2."
    }
    with open(os.path.join(chunker.processed_dir, "test.json"), "w") as f:
        json.dump(dummy_data, f)
        
    all_chunks = chunker.process_and_tag()
    
    assert len(all_chunks) == 2
    assert all_chunks[0]["text"] == "Fact 1."
    assert all_chunks[0]["metadata"]["fund_name"] == "Test Fund"
    assert all_chunks[0]["metadata"]["source_url"] == "http://example.com"
    assert all_chunks[0]["metadata"]["last_updated"] == "2023-01-01"
