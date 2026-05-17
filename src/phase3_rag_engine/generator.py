"""Phase 3.3 and 3.4: LLM Prompting and Response Generation."""
import json
import os
import logging
from groq import (
    Groq,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
    APIStatusError,
)
from dotenv import load_dotenv
from src.phase3_rag_engine.retriever import FactRetriever, RELEVANCE_MAX_DISTANCE, pick_source_chunk
from src.phase3_rag_engine.query_policy import (
    classify_query,
    filter_chunks_for_query,
    filter_metrics_for_query,
    can_show_source,
    _available_funds_hint,
)
from src.phase4_guardrails.guardrails import InputGuard, OutputGuard

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

USER_UNAVAILABLE_MSG = (
    "The assistant is temporarily unavailable. Please try again in a few minutes."
)

load_dotenv()
if not os.environ.get("GROQ_API_KEY", "").strip():
    logging.warning(
        "GROQ_API_KEY is not set. Add it to .env locally or to Railway service variables."
    )


def _structured_error(status: str = "error", message: str | None = None) -> dict:
    return {
        "answer": message or USER_UNAVAILABLE_MSG,
        "metrics": {},
        "source": None,
        "show_source": False,
        "status": status,
    }


def _is_context_relevant(chunks: list) -> bool:
    if not chunks:
        return False
    return chunks[0].get("distance", float("inf")) <= RELEVANCE_MAX_DISTANCE


def _no_context_response() -> dict:
    return {
        "answer": "I do not have the information to answer that.",
        "metrics": {},
        "source": None,
        "show_source": False,
        "status": "no_context",
    }


def _groq_error_response(exc: Exception) -> dict:
    if isinstance(exc, AuthenticationError):
        logging.error("Groq authentication failed — check GROQ_API_KEY on Railway.")
        return _structured_error("config_error")
    if isinstance(exc, RateLimitError):
        logging.error("Groq rate limit exceeded: %s", exc)
        return _structured_error("rate_limited")
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        logging.error("Groq connection failed: %s", exc)
        return _structured_error()
    if isinstance(exc, APIStatusError):
        logging.error("Groq API error (%s): %s", exc.status_code, exc)
        return _structured_error()
    logging.error("Unexpected generation error: %s", exc)
    return _structured_error()


def _build_json_prompt(query: str, context_chunks: list, fund_name: str | None) -> str:
    context_text = "\n".join(f"- {chunk['text']}" for chunk in context_chunks)
    fund_rule = (
        f'Answer ONLY about "{fund_name}". Do NOT mention or compare other funds.'
        if fund_name
        else "Answer only from the context provided."
    )
    return f"""You are a factual HDFC Mutual Fund FAQ assistant.

Rules:
1. {fund_rule}
2. Answer ONLY what the user asked — do not list extra metrics or facts they did not request.
3. Use ONLY the Context below. If the answer is not in Context, say: "I do not have the information to answer that."
4. Maximum 2 sentences in "answer".
5. In "metrics", include ONLY fields the user asked about (leave others out entirely).

Context:
{context_text}

Return EXACTLY this JSON (omit metric keys you were not asked about):
{{
  "answer": "Your concise factual answer naming the fund.",
  "metrics": {{}}
}}
"""


class RAGGenerator:
    def __init__(self, retriever=None, model="llama-3.1-8b-instant"):
        self.retriever = retriever or FactRetriever()
        self.model = model
        self.input_guard = InputGuard()
        self.output_guard = OutputGuard()

        self.api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not self.api_key:
            logging.warning("GROQ_API_KEY is missing or empty.")

        self.client = (
            Groq(api_key=self.api_key, timeout=60.0, max_retries=2)
            if self.api_key
            else None
        )

    def generate_structured_response(self, query: str) -> dict:
        is_safe, msg = self.input_guard.check_query(query)
        if not is_safe:
            return {
                "answer": msg,
                "metrics": {},
                "source": None,
                "show_source": False,
                "status": "blocked",
            }

        policy = classify_query(query)

        if policy["kind"] == "off_topic":
            return {
                "answer": (
                    "I can only answer factual questions about specific HDFC mutual funds "
                    "in my knowledge base (expense ratio, NAV, exit load, etc.). "
                    + _available_funds_hint()
                ),
                "metrics": {},
                "source": None,
                "show_source": False,
                "status": "blocked",
            }

        if policy["kind"] == "needs_fund":
            return {
                "answer": _available_funds_hint(),
                "metrics": {},
                "source": None,
                "show_source": False,
                "status": "needs_fund",
            }

        if not self.client:
            return _structured_error("config_error")

        chunks = self.retriever.retrieve_context(
            query, fund_slug=policy["fund_slug"]
        )
        chunks = filter_chunks_for_query(query, chunks)

        if not chunks or not _is_context_relevant(chunks):
            return _no_context_response()

        json_prompt = _build_json_prompt(query, chunks, policy["fund_name"])

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": json_prompt},
                    {"role": "user", "content": query},
                ],
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            result = json.loads(chat_completion.choices[0].message.content)
            result["answer"] = self.output_guard.check_response(
                result.get("answer", "")
            )

            if "flagged by safety guardrails" in result["answer"].lower():
                result["metrics"] = {}
                result["source"] = None
                result["show_source"] = False
                result["status"] = "blocked"
                return result

            raw_metrics = result.get("metrics") or {}
            result["metrics"] = filter_metrics_for_query(query, raw_metrics)
            result["status"] = "success"

            source_chunk = pick_source_chunk(query, chunks)
            if can_show_source(query, chunks, result["answer"], result["status"]) and source_chunk:
                meta = source_chunk["metadata"]
                result["source"] = {
                    "fund_name": meta.get("fund_name"),
                    "url": meta.get("source_url"),
                    "last_updated": meta.get("last_updated", "").split("T")[0],
                }
                result["show_source"] = True
            else:
                result["source"] = None
                result["show_source"] = False
                if "i do not have the information" in result["answer"].lower():
                    result["status"] = "no_context"

            return result

        except (APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError, APIStatusError) as e:
            return _groq_error_response(e)
        except Exception as e:
            return _groq_error_response(e)

    def generate_response(self, query: str) -> str:
        structured = self.generate_structured_response(query)
        answer = structured.get("answer", "")
        if structured.get("show_source") and structured.get("source"):
            src = structured["source"]
            answer += (
                f"\n\n*Last updated: {src.get('last_updated', '')} | "
                f"[{src.get('fund_name', 'Source')}]({src.get('url', '#')})*"
            )
        return answer
