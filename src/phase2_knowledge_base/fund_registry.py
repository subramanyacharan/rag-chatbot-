"""Canonical fund metadata for scraping, chunking, and retrieval."""

FUND_REGISTRY = [
    {
        "slug": "hdfc-mid-cap-fund-direct-growth",
        "fund_name": "HDFC Mid Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "aliases": [
            "mid cap",
            "mid-cap",
            "midcap",
            "mid cap opportunities",
            "mid cap fund",
        ],
    },
    {
        "slug": "hdfc-equity-fund-direct-growth",
        "fund_name": "HDFC Equity Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "aliases": [
            "equity fund",
            "equity savings",
            "hdfc equity",
        ],
    },
    {
        "slug": "hdfc-focused-fund-direct-growth",
        "fund_name": "HDFC Focused Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
        "aliases": [
            "focused fund",
            "focused 30",
            "hdfc focused",
        ],
    },
    {
        "slug": "hdfc-elss-tax-saver-fund-direct-plan-growth",
        "fund_name": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "aliases": [
            "elss",
            "tax saver",
            "tax-saver",
            "tax saver fund",
        ],
    },
    {
        "slug": "hdfc-large-cap-fund-direct-growth",
        "fund_name": "HDFC Large Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "aliases": [
            "large cap",
            "large-cap",
            "top 100",
            "hdfc large cap",
        ],
    },
]

SLUG_TO_FUND = {f["slug"]: f for f in FUND_REGISTRY}


def fund_from_slug(slug: str) -> dict | None:
    return SLUG_TO_FUND.get(slug)


def detect_fund_slug(query: str) -> str | None:
    """Return the best-matching fund slug for a user query, if any."""
    q = query.lower()
    best_slug = None
    best_len = 0
    for fund in FUND_REGISTRY:
        for alias in fund["aliases"]:
            if alias in q and len(alias) > best_len:
                best_len = len(alias)
                best_slug = fund["slug"]
    if best_slug:
        return best_slug
    for fund in FUND_REGISTRY:
        slug_words = fund["slug"].replace("-", " ")
        name_words = fund["fund_name"].lower()
        if slug_words in q or name_words in q:
            return fund["slug"]
    return None
