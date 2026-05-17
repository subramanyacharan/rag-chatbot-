import json
import pytest
from unittest.mock import patch, MagicMock
from groq import APIConnectionError
from src.phase3_rag_engine.generator import RAGGenerator, USER_UNAVAILABLE_MSG

@pytest.fixture
def mock_retriever():
    retriever = MagicMock()
    retriever.retrieve_context.return_value = [
        {
            "text": "The expense ratio is 0.73%.",
            "metadata": {
                "source_url": "http://example.com/hdfc-midcap",
                "last_updated": "2026-05-05T12:00:00",
                "fund_name": "HDFC Mid Cap Fund Direct Growth",
                "fund_slug": "hdfc-mid-cap-fund-direct-growth",
            },
            "distance": 0.2,
        }
    ]
    return retriever

def test_build_json_prompt(mock_retriever):
    chunks = mock_retriever.retrieve_context.return_value
    prompt = __import__(
        "src.phase3_rag_engine.generator", fromlist=["_build_json_prompt"]
    )._build_json_prompt(
        "What is the NAV of HDFC Mid Cap?",
        chunks,
        "HDFC Mid Cap Fund Direct Growth",
    )
    assert "The expense ratio is 0.73%." in prompt
    assert "ONLY what the user asked" in prompt
    assert "HDFC Mid Cap Fund Direct Growth" in prompt

@patch("src.phase3_rag_engine.generator.Groq")
def test_generate_response(mock_groq_class, mock_retriever):
    # Setup mock Groq client
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_message = MagicMock()
    
    mock_message.content = json.dumps({
        "answer": "The expense ratio of HDFC Mid Cap Fund Direct Growth is 0.73%.",
        "metrics": {"Expense Ratio": "0.73%"},
    })
    mock_completion.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_completion

    mock_groq_class.return_value = mock_client

    generator = RAGGenerator(retriever=mock_retriever)
    generator.client = mock_client

    mock_retriever.retrieve_context.return_value = [
        {
            "text": "The expense ratio of HDFC Mid Cap Fund Direct Growth is 0.73%.",
            "metadata": {
                "fund_slug": "hdfc-mid-cap-fund-direct-growth",
                "fund_name": "HDFC Mid Cap Fund Direct Growth",
                "source_url": "http://example.com/hdfc-midcap",
                "last_updated": "2026-05-05T12:00:00",
            },
            "distance": 0.2,
        }
    ]
    response = generator.generate_response(
        "What is the expense ratio of HDFC Mid Cap Fund?"
    )
    
    # Assert LLM was called
    mock_client.chat.completions.create.assert_called_once()
    
    # Assert response and footer
    assert "0.73%" in response
    assert "Last updated: 2026-05-05" in response
    assert "[HDFC Mid Cap Fund Direct Growth](http://example.com/hdfc-midcap)" in response


@patch("src.phase3_rag_engine.generator.Groq")
def test_structured_response_groq_connection_error(mock_groq_class, mock_retriever):
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = APIConnectionError(request=MagicMock())
    mock_groq_class.return_value = mock_client

    generator = RAGGenerator(retriever=mock_retriever)
    generator.client = mock_client

    result = generator.generate_structured_response("What is the NAV of HDFC Mid Cap Fund?")

    assert result["status"] == "error"
    assert result["answer"] == USER_UNAVAILABLE_MSG
    assert "Connection error" not in result["answer"]


@patch("src.phase3_rag_engine.generator.Groq")
def test_structured_response_irrelevant_retrieval(mock_groq_class, mock_retriever):
    mock_retriever.retrieve_context.return_value = [
        {
            "text": "Unrelated fund data.",
            "metadata": {
                "fund_name": "HDFC Mid Cap Fund Direct Growth",
                "fund_slug": "hdfc-mid-cap-fund-direct-growth",
                "source_url": "http://x.com",
                "last_updated": "2026-01-01",
            },
            "distance": 2.5,
        }
    ]
    generator = RAGGenerator(retriever=mock_retriever)
    generator.client = MagicMock()

    result = generator.generate_structured_response(
        "What is the expense ratio of HDFC Mid-Cap Fund?"
    )

    assert result["status"] == "no_context"
    assert result["show_source"] is False
    assert result["source"] is None
    mock_groq_class.return_value.chat.completions.create.assert_not_called()


def test_structured_response_needs_fund(mock_retriever):
    generator = RAGGenerator(retriever=mock_retriever)
    generator.client = MagicMock()
    result = generator.generate_structured_response("what is the expense ratio?")
    assert result["status"] == "needs_fund"
    assert result["show_source"] is False
    mock_retriever.retrieve_context.assert_not_called()
