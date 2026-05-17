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

OFF_TOPIC_PATTERNS = [
    r"\b(i love you|marry me|date me|how are you)\b",
    r"\b(weather|temperature|forecast)\b",
    r"\b(recipe|cook|bake)\b",
    r"\b(movie|netflix|song lyrics)\b",
    r"\b(write (me )?a poem|tell (me )?a joke)\b",
    r"\b(who (is|was) (the )?president of)\b",
    r"\b(football|cricket score|ipl match)\b",
    r"^(hi|hello|hey)[\s!.?]*$",
    r"\b(compare all|all funds|every fund|list all funds)\b",
]

SOURCE_MAX_DISTANCE = float(__import__("os").environ.get("SOURCE_MAX_DISTANCE", "0.52"))


def _available_funds_hint() -> str:
    names = [f["fund_name"] for f in FUND_REGISTRY]
    return (
        "Please name the specific HDFC fund in your question. "
        f"I can answer for: {', '.join(names)}."
    )


def is_off_topic(query: str) -> bool:
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
    if not _mentions_allowed_topic(q):
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
    fund_slug = detect_fund_slug(query)
    if is_off_topic(query):
        return {
            "kind": "off_topic",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
        }
    if needs_fund_specification(query):
        return {
            "kind": "needs_fund",
            "fund_slug": None,
            "fund_name": None,
            "show_source": False,
        }
    fund = fund_from_slug(fund_slug) if fund_slug else None
    return {
        "kind": "fund_specific",
        "fund_slug": fund_slug,
        "fund_name": fund["fund_name"] if fund else None,
        "show_source": True,
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
