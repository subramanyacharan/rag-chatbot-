from src.phase2_knowledge_base.fund_registry import detect_fund_slug


def test_detect_mid_cap():
    assert detect_fund_slug("HDFC Mid Cap Fund Direct Growth NAV") == (
        "hdfc-mid-cap-fund-direct-growth"
    )


def test_detect_elss():
    assert detect_fund_slug("HDFC ELSS tax saver exit load") == (
        "hdfc-elss-tax-saver-fund-direct-plan-growth"
    )


def test_detect_none_for_unknown():
    assert detect_fund_slug("What is inflation?") is None
