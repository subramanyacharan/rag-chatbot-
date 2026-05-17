import os
import json
import pytest
from src.phase2_knowledge_base.extractor import FactExtractor

@pytest.fixture
def extractor(tmp_path):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()
    return FactExtractor(str(raw_dir), str(processed_dir))

def test_extract_facts(extractor):
    sample_text = "NAV: 04 May '26 ₹218.53 Min. for SIP ₹100 Fund size (AUM) ₹85,357.92 Cr Expense ratio 0.73% Rating 5 Exit load of 1% if redeemed within 1 year. Fund benchmark NIFTY Midcap 150 Total Return Index Scheme Information The HDFC Mid Cap Fund Direct Growth is rated Very High risk. Chirag Setalvad is the Current Fund Manager"
    facts = extractor.extract_facts(sample_text)
    
    assert facts['nav'] == "₹218.53"
    assert facts['min_sip'] == "₹100"
    assert facts['aum'] == "₹85,357.92 Cr"
    assert facts['expense_ratio'] == "0.73%"
    assert facts['exit_load'] == "Exit load of 1% if redeemed within 1 year."
    assert facts['benchmark'] == "NIFTY Midcap 150 Total Return Index"
    assert facts['risk'] == "Very High risk"
    assert facts['fund_manager'] == "Chirag Setalvad"

def test_generate_sentences(extractor):
    facts = {'expense_ratio': '0.73%', 'nav': '₹218.53'}
    sentences = extractor.generate_sentences("Test Fund", facts)
    assert "The expense ratio of Test Fund is 0.73%." in sentences
    assert "The latest NAV of Test Fund is ₹218.53." in sentences
