"""Phase 4.1 and 4.2: Input and Output Guardrails."""
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class InputGuard:
    def __init__(self):
        # Keywords that indicate an advisory intent or prediction
        self.advisory_patterns = [
            r"\b(should i invest)\b",
            r"\b(is this a good)\b",
            r"\b(recommend)\b",
            r"\b(best fund)\b",
            r"\b(which fund to buy)\b",
            r"\b(will it go up)\b",
            r"\b(double my money)\b",
            r"\b(safe investment)\b",
            r"\b(predict)\b",
            r"\b(allocate my portfolio)\b"
        ]
        
    def check_query(self, query: str) -> tuple[bool, str]:
        """
        Phase 4.1: Check if the user query violates constraints.
        Returns (is_safe: bool, violation_message: str)
        """
        lower_query = query.lower()
        
        for pattern in self.advisory_patterns:
            if re.search(pattern, lower_query):
                logging.warning(f"Input Guardrail triggered by pattern: {pattern}")
                return False, "I am a factual assistant and cannot provide investment advice or recommendations. Please consult a SEBI-registered financial advisor."
                
        return True, ""


class OutputGuard:
    def __init__(self):
        # Keywords that the LLM shouldn't generate in a factual context
        self.banned_phrases = [
            r"\b(i recommend)\b",
            r"\b(you should invest)\b",
            r"\b(guaranteed returns)\b",
            r"\b(surefire way)\b",
            r"\b(buy this)\b",
            r"\b(highly recommended)\b"
        ]

    def check_response(self, response: str) -> str:
        """
        Phase 4.2: Post-generation check for hallucinations or advice.
        If a banned phrase is found, override the response.
        """
        lower_resp = response.lower()
        
        for pattern in self.banned_phrases:
            if re.search(pattern, lower_resp):
                logging.warning(f"Output Guardrail triggered by pattern: {pattern}")
                return "The generated response was flagged by safety guardrails for potentially containing investment advice. As a factual assistant, I cannot provide this information."
                
        return response
