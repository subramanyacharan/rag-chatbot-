"""Classify queries and enforce fund-specific response rules."""
import re

from src.phase2_knowledge_base.fund_registry import FUND_REGISTRY, detect_fund_slug, fund_from_slug

TOPIC_KEYWORDS = (
    "expense ratio",
    "exit load",
    "nav",
    "aum",
    "sip",
    "benchmark",
    "fund manager",
    "riskometer",
    "risk",
    "lock-in",
    "lock in",
    "minimum investment",
    "mutual fund",
)

# Patterns for queries that are completely off-topic (non-financial)
OFF_TOPIC_PATTERNS = [
    r"\b(i love you|marry me|date me|how are you)\b",
    r"\b(weather|temperature|forecast)\b",
    r"\b(recipe|cook|bake)\b",
    r"\b(movie|netflix|song lyrics)\b",
    r"\b(write (me )?a poem|tell (me )?a joke)\b",
    r"\b(who (is|was) (the )?president of)\b",
    r"\b(football|cricket score|ipl match)\b",
]

# Patterns for simple greetings
GREETING_PATTERNS = [
    r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening)[\s!.?]*$",
]

# Patterns for queries about funds not in our HDFC corpus
OTHER_AMC_PATTERNS = [
    r"\b(sbi|icici|axis|kotak|franklin|aditya birla|tata|uti|lic|nippon|idfc|bandhan|bank of india|canara robeco|dsp|hsbc|itgi|jm financial|mahindra|mirae|mohit|pgim|quant|sundaram|white oak|worldequi)\b.*\b(fund|mutual)\b",
    r"\b(sbi small cap|sbi large cap|sbi flexi cap|sbi hybrid)\b",
    r"\b(icici prudential|icici blue chip|icici technology)\b",
    r"\b(axis midcap|axis smallcap|axis bluechip)\b",
    r"\b(kotak flexicap|kotak emerging)\b",
    r"\b(franklin templeton|franklin india)\b",
]

# Patterns for personal/account-specific queries
PERSONAL_QUERY_PATTERNS = [
    r"\b(my balance|my holding|my account|my statement|my portfolio|my investment)\b",
    r"\b(my tax|my units|my nav|my redemption)\b",
    r"\b(check my|show my|view my|my hdfc)\b",
    r"\b(how much (do i have|did i invest|is my))\b",
]

# Patterns for PII (Personally Identifiable Information)
PII_PATTERNS = [
    r"\b(pan is|pan number|pan:|aadhaar is|aadhaar number|aadhaar:)\b",
    r"\b([a-z]{5}[0-9]{4}[a-z]{1})\b",  # PAN format
    r"\b(\d{4}[ -]?\d{4}[ -]?\d{4})\b",  # Aadhaar-like pattern
    r"\b(phone|mobile|contact|email)\b.*\b(\d{10}|@)\b",
    r"\b(account number|acc no|customer id)\b",
    r"\b(otp|one time password)\b",
]

# Patterns for performance/return queries
PERFORMANCE_PATTERNS = [
    r"\b(returns?|cagr|xirr|performance|perform)\b",
    r"\b(1-year|2-year|3-year|5-year|10-year|annualized)\b.*\b(return|growth)\b",
    r"\b(highest return|best return|top return)\b",
    r"\b(performance chart|performance graph|nav history)\b",
    r"\b(how (much|many).*(grow|increase|return))\b",
]

# Patterns for comparison queries
COMPARISON_PATTERNS = [
    r"\b(which is better|which one is better|better than)\b",
    r"\b(compare|vs|versus)\b.*\b(and|with)\b",
    r"\b(lowest expense|highest return|best performer)\b",
    r"\b(difference between|difference in)\b",
]

# Patterns for portfolio/allocation queries
PORTFOLIO_PATTERNS = [
    r"\b(allocate|allocation|portfolio construction|asset allocation)\b",
    r"\b(diversify|diversification|ideal mix|optimal mix)\b",
    r"\b(percentage|how much).*(invest|allocate)\b",
    r"\b(create (a )?portfolio|build (a )?portfolio)\b",
]

# Patterns for prediction/forecast queries
PREDICTION_PATTERNS = [
    r"\b(will it|will the|will hdfc)\b.*\b(go up|rise|fall|drop|increase|decrease)\b",
    r"\b(predict|forecast|future|next year|next month)\b",
    r"\b(outperform|underperform|beat the market)\b",
    r"\b(will (it|this|the fund).*(be good|be safe|give returns))\b",
]

# Patterns for historical data queries
HISTORICAL_PATTERNS = [
    r"\b(was the|what was)\b.*\b(on (january|february|march|april|may|june|july|august|september|october|november|december)|\d{1,2}/\d{1,2}/\d{4})\b",
    r"\b(historical|past|previous|old)\b.*\b(nav|expense|aum)\b",
    r"\b(last year|last month|previous year)\b.*\b(data|information)\b",
]

# Patterns for fund holdings queries
HOLDINGS_PATTERNS = [
    r"\b(holdings?|portfolio composition|stocks?|securities?)\b.*\b(in|of|held by)\b",
    r"\b(top 10|top holdings|underlying stocks)\b",
    r"\b(what stocks|which companies|what companies)\b.*\b(invested)\b",
]

# Patterns for generic mutual fund questions (without HDFC)
GENERIC_MF_PATTERNS = [
    r"^(what is|explain|tell me about)\b.*(mutual fund|sip|nav|expense ratio|exit load)\b$",
    r"\b(how do (mutual funds|sip))\b.*(work|function)\b",
    r"\b(definition|meaning of)\b.*(mutual fund|sip|nav)\b",
]

SOURCE_MAX_DISTANCE = float(__import__("os").environ.get("SOURCE_MAX_DISTANCE", "0.52"))


def _available_funds_hint() -> str:
    names = [f["fund_name"] for f in FUND_REGISTRY]
    return (
        "Please name the specific HDFC fund in your question. "
        f"I can answer for: {', '.join(names)}."
    )


def is_off_topic(query: str) -> bool:
    """Check if query is completely off-topic (non-financial)."""
    q = query.lower().strip()
    if not q:
        return True
    if detect_fund_slug(query):
        return False
    if "hdfc" in q and any(kw in q for kw in TOPIC_KEYWORDS):
        return False
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, q):
            return True
    if is_greeting(q):
        return False
    if not _mentions_allowed_topic(q):
        return True
    return False


def is_greeting(query: str) -> bool:
    """Check if query is a simple greeting."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_other_amc(query: str) -> bool:
    """Check if query is about funds from other AMCs not in our corpus."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in OTHER_AMC_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_personal_query(query: str) -> bool:
    """Check if query is about personal account information."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in PERSONAL_QUERY_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def contains_pii(query: str) -> bool:
    """Check if query contains PII (PAN, Aadhaar, phone, email, etc.)."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in PII_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_performance_query(query: str) -> bool:
    """Check if query asks about performance/returns."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in PERFORMANCE_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_comparison_query(query: str) -> bool:
    """Check if query asks to compare funds."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in COMPARISON_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_portfolio_query(query: str) -> bool:
    """Check if query asks about portfolio allocation."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in PORTFOLIO_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_prediction_query(query: str) -> bool:
    """Check if query asks for predictions/forecasts."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in PREDICTION_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_historical_query(query: str) -> bool:
    """Check if query asks for historical data."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in HISTORICAL_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_holdings_query(query: str) -> bool:
    """Check if query asks about fund holdings/composition."""
    q = query.lower().strip()
    if not q:
        return False
    for pattern in HOLDINGS_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def is_generic_mf_query(query: str) -> bool:
    """Check if query is a generic mutual fund question without HDFC context."""
    q = query.lower().strip()
    if not q:
        return False
    if "hdfc" in q:
        return False
    for pattern in GENERIC_MF_PATTERNS:
        if re.search(pattern, q):
            return True
    return False


def _mentions_allowed_topic(q: str) -> bool:
    if "hdfc" in q:
        return True
    return any(kw in q for kw in TOPIC_KEYWORDS)


def needs_fund_specification(query: str) -> bool:
    """True when on-topic but no identifiable fund in the query."""
    if detect_fund_slug(query):
        return False
    return _mentions_allowed_topic(query.lower())


def classify_query(query: str) -> dict:
    """Classify query into categories with strict filtering."""
    fund_slug = detect_fund_slug(query)
    
    # Priority 1: PII and privacy violations
    if contains_pii(query):
        return {
            "kind": "pii_violation",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": "Query contains personally identifiable information (PAN, Aadhaar, phone, email, etc.)",
        }
    
    # Priority 2: Greetings
    if is_greeting(query):
        return {
            "kind": "greeting",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": None,
        }
    
    # Priority 3: Personal/account queries
    if is_personal_query(query):
        return {
            "kind": "personal_query",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": "Query asks for personal account information which is not accessible",
        }
    
    # Priority 3: Other AMC funds (not in corpus)
    if is_other_amc(query):
        return {
            "kind": "other_amc",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": "Query asks about funds from other AMCs not in the knowledge base",
        }
    
    # Priority 4: Performance queries
    if is_performance_query(query):
        return {
            "kind": "performance_query",
            "fund_slug": fund_slug,
            "fund_name": fund_from_slug(fund_slug)["fund_name"] if fund_slug else None,
            "show_source": False,
            "reason": "Performance data changes frequently. Please check the official factsheet for performance information.",
        }
    
    # Priority 5: Comparison queries
    if is_comparison_query(query):
        return {
            "kind": "comparison_query",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": "Comparisons require subjective judgment. I can only provide factual information about individual funds.",
        }
    
    # Priority 6: Portfolio/allocation queries
    if is_portfolio_query(query):
        return {
            "kind": "portfolio_query",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": "Portfolio construction requires personalized financial advice from a SEBI-registered advisor.",
        }
    
    # Priority 7: Prediction/forecast queries
    if is_prediction_query(query):
        return {
            "kind": "prediction_query",
            "fund_slug": fund_slug,
            "fund_name": fund_from_slug(fund_slug)["fund_name"] if fund_slug else None,
            "show_source": False,
            "reason": "I cannot predict future market movements or fund performance.",
        }
    
    # Priority 8: Historical data queries
    if is_historical_query(query):
        return {
            "kind": "historical_query",
            "fund_slug": fund_slug,
            "fund_name": fund_from_slug(fund_slug)["fund_name"] if fund_slug else None,
            "show_source": False,
            "reason": "Historical data is not available in the knowledge base. Please check official factsheets.",
        }
    
    # Priority 9: Fund holdings queries
    if is_holdings_query(query):
        return {
            "kind": "holdings_query",
            "fund_slug": fund_slug,
            "fund_name": fund_from_slug(fund_slug)["fund_name"] if fund_slug else None,
            "show_source": False,
            "reason": "Portfolio composition changes frequently and is not available in the knowledge base.",
        }
    
    # Priority 10: Generic mutual fund questions
    if is_generic_mf_query(query):
        return {
            "kind": "generic_mf",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": "I can only answer questions about specific HDFC funds. Please specify the fund name.",
        }
    
    # Priority 11: Completely off-topic
    if is_off_topic(query):
        return {
            "kind": "off_topic",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": "Query is off-topic. I can only answer factual questions about HDFC mutual funds.",
        }
    
    # Priority 12: Needs fund specification
    if needs_fund_specification(query):
        return {
            "kind": "needs_fund",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
            "reason": "Please specify which HDFC fund you're asking about. " + _available_funds_hint(),
        }
    
    # Default: Fund-specific query
    fund = fund_from_slug(fund_slug) if fund_slug else None
    return {
        "kind": "fund_specific",
        "fund_slug": fund_slug,
        "fund_name": fund["fund_name"] if fund else None,
        "show_source": True,
        "reason": None,
    }


def filter_chunks_for_query(query: str, chunks: list, max_chunks: int = 3) -> list:
    """Keep only chunks that match the asked metric and target fund."""
    if not chunks:
        return []

    q = query.lower()
    fund_slug = detect_fund_slug(query)
    if fund_slug:
        chunks = [c for c in chunks if c["metadata"].get("fund_slug") == fund_slug]

    intent_filters = [
        (("nav",), lambda t: "nav" in t.lower()),
        (("expense", "ratio"), lambda t: "expense ratio" in t.lower()),
        (("exit load", "exit-load"), lambda t: "exit load" in t.lower()),
        (("sip", "minimum"), lambda t: "sip" in t.lower() or "minimum" in t.lower()),
        (("aum", "fund size"), lambda t: "aum" in t.lower() or "fund size" in t.lower()),
        (("benchmark",), lambda t: "benchmark" in t.lower()),
        (("manager",), lambda t: "fund manager" in t.lower() or "manager" in t.lower()),
        (("risk", "riskometer"), lambda t: "risk" in t.lower()),
    ]
    for keys, predicate in intent_filters:
        if any(k in q for k in keys):
            matched = [c for c in chunks if predicate(c["text"])]
            if matched:
                chunks = matched
            break

    return chunks[:max_chunks]


def filter_metrics_for_query(query: str, metrics: dict) -> dict:
    """Return only metrics the user asked about."""
    if not metrics:
        return {}
    q = query.lower()
    allowed = {}
    rules = [
        (("expense", "ratio"), "Expense Ratio"),
        (("exit load", "exit-load"), "Exit Load"),
        (("nav",), "NAV"),
        (("aum", "fund size"), "AUM"),
        (("sip", "minimum"), "Minimum SIP"),
        (("benchmark",), "Benchmark"),
        (("manager",), "Fund Manager"),
        (("risk", "riskometer"), "Risk"),
    ]
    asked_any = False
    for keys, label in rules:
        if any(k in q for k in keys):
            asked_any = True
            val = metrics.get(label)
            if val and str(val).lower() not in ("val", "n/a", "null", ""):
                allowed[label] = val
    if asked_any:
        return allowed
    return {}


def can_show_source(query: str, chunks: list, answer: str, status: str) -> bool:
    policy = classify_query(query)
    if not policy["show_source"] or status != "success":
        return False
    if not chunks or not detect_fund_slug(query):
        return False
    if chunks[0].get("distance", 999) > SOURCE_MAX_DISTANCE:
        return False

    slug = detect_fund_slug(query)
    if not all(c["metadata"].get("fund_slug") == slug for c in chunks):
        return False

    lower = answer.lower()
    block_markers = (
        "i do not have the information",
        "please name the specific",
        "knowledge base",
        "cannot provide investment",
        "flagged by safety",
    )
    if any(m in lower for m in block_markers):
        return False

    return True
