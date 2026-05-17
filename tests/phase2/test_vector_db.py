import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.phase2_knowledge_base.vector_db import VectorDBManager

@pytest.fixture
def mock_db_manager(tmp_path):
    chunks_file = tmp_path / "test_chunks.json"
    db_dir = tmp_path / "test_db"
    
    # Create dummy chunks
    dummy_chunks = [
        {"text": "Fact 1", "metadata": {"fund_name": "Fund A"}},
        {"text": "Fact 2", "metadata": {"fund_name": "Fund B"}}
    ]
    with open(chunks_file, "w") as f:
        json.dump(dummy_chunks, f)
        
    with patch('src.phase2_knowledge_base.vector_db.get_embedding_model') as mock_model_fn, \
         patch('src.phase2_knowledge_base.vector_db.chromadb.PersistentClient') as mock_chroma:

        mock_instance = MagicMock()
        mock_instance.encode.return_value = [[0.1] * 384, [0.2] * 384]
        mock_model_fn.return_value = mock_instance

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client.delete_collection.return_value = None
        mock_chroma.return_value = mock_client
        
        manager = VectorDBManager(str(chunks_file), str(db_dir))
        return manager

def test_process_and_store(mock_db_manager):
    mock_db_manager.process_and_store()
    
    # Verify collection upsert was called
    mock_db_manager.collection.upsert.assert_called_once()
    
    args, kwargs = mock_db_manager.collection.upsert.call_args
    assert len(kwargs['documents']) == 2
    assert kwargs['documents'][0] == "Fact 1"
    assert len(kwargs['embeddings']) == 2
    assert len(kwargs['embeddings'][0]) == 384
