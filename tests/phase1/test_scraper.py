import os
import json
import pytest
from unittest.mock import patch, Mock
from src.phase1_data_collection.scraper import FundScraper

@pytest.fixture
def mock_output_dir(tmp_path):
    return str(tmp_path / "raw")

def test_fetch_page_success(mock_output_dir):
    scraper = FundScraper(["http://example.com"], mock_output_dir)
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_get.return_value = mock_response
        
        result = scraper.fetch_page("http://example.com")
        assert result == "<html><body>Test</body></html>"

def test_fetch_page_failure(mock_output_dir):
    scraper = FundScraper(["http://example.com"], mock_output_dir)
    with patch("requests.get") as mock_get:
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = scraper.fetch_page("http://example.com")
        assert result is None

def test_extract_text(mock_output_dir):
    scraper = FundScraper([], mock_output_dir)
    html = "<html><head><script>alert(1);</script></head><body><h1>Hello</h1><p>World</p></body></html>"
    text = scraper.extract_text(html)
    assert text == "Hello World"

def test_scraper_run(mock_output_dir):
    urls = ["http://example.com/fund-1"]
    scraper = FundScraper(urls, mock_output_dir)
    
    with patch.object(scraper, "fetch_page", return_value="<html><body>Content</body></html>"):
        scraper.run()
        
        # Check if file was created
        expected_file = os.path.join(mock_output_dir, "fund-1.json")
        assert os.path.exists(expected_file)
        
        with open(expected_file, "r") as f:
            data = json.load(f)
            assert data["url"] == "http://example.com/fund-1"
            assert data["raw_text"] == "Content"
            assert "last_updated" in data
