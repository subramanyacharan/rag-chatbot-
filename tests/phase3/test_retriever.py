import pytest
from unittest.mock import patch, MagicMock
from src.phase3_rag_engine.retriever import FactRetriever

@pytest.fixture
def mock_retriever():
    with patch('src.phase3_rag_engine.retriever.ensure_vector_db_populated'), \
         patch('src.phase3_rag_engine.retriever.get_embedding_model') as mock_model_fn, \
         patch('src.phase3_rag_engine.retriever.chromadb.PersistentClient') as mock_chroma:

        mock_instance = MagicMock()
        mock_instance.encode.return_value = [[0.1] * 384]
        mock_model_fn.return_value = mock_instance
        
        mock_client = MagicMock()
        mock_collection = MagicMock()
        
        # Mock chroma query return format
        mock_collection.query.return_value = {
            'documents': [['Fact A', 'Fact B']],
            'metadatas': [[
                {'source_url': 'url1', 'fund_slug': 'fund-a'},
                {'source_url': 'url2', 'fund_slug': 'fund-b'},
            ]],
            'distances': [[0.2, 0.4]]
        }
        
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chroma.return_value = mock_client
        
        retriever = FactRetriever("dummy_path")
        return retriever

def test_retrieve_context(mock_retriever):
    results = mock_retriever.retrieve_context("Test query", top_k=2)
    
    # Ensure query processing (3.1) was called
    mock_retriever.model.encode.assert_called()
    
    # Ensure semantic retrieval (3.2) was called
    mock_retriever.collection.query.assert_called_once()
    
    # Check formatting
    assert len(results) == 2
    assert results[0]['text'] == 'Fact A'
    assert results[0]['distance'] == 0.2
    assert results[0]['metadata']['source_url'] == 'url1'
