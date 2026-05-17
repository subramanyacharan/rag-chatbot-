from src.phase3_rag_engine.query_policy import (
    classify_query,
    can_show_source,
    filter_metrics_for_query,
    is_off_topic,
    needs_fund_specification,
)


def test_off_topic_greeting():
    assert is_off_topic("hello") is True
    assert classify_query("hello")["kind"] == "off_topic"


def test_needs_fund_without_name():
    assert needs_fund_specification("what is the expense ratio?") is True
    assert classify_query("what is the expense ratio?")["kind"] == "needs_fund"


def test_fund_specific_query():
    policy = classify_query("HDFC Mid Cap Fund NAV")
    assert policy["kind"] == "fund_specific"
    assert policy["fund_slug"] == "hdfc-mid-cap-fund-direct-growth"
    assert policy["show_source"] is True


def test_filter_metrics_only_asked():
    metrics = {
        "Expense Ratio": "0.75%",
        "NAV": "100",
        "Exit Load": "1%",
    }
    filtered = filter_metrics_for_query("What is the NAV of HDFC Mid Cap?", metrics)
    assert "NAV" in filtered
    assert "Expense Ratio" not in filtered


def test_can_show_source_requires_fund_in_query():
    chunks = [
        {
            "text": "NAV is 100",
            "metadata": {"fund_slug": "hdfc-equity-fund-direct-growth"},
            "distance": 0.3,
        }
    ]
    assert can_show_source("what is nav?", chunks, "The NAV is 100.", "success") is False
