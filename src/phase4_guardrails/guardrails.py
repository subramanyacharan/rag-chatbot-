"""Phase 4.1 and 4.2: Input and Output Guardrails."""
import re
import logging

from src.phase3_rag_engine.query_policy import is_off_topic, _available_funds_hint

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class InputGuard:
    def __init__(self):
        # Comprehensive advisory and recommendation patterns
        self.advisory_patterns = [
            r"\b(should i invest)\b",
            r"\b(is this a good)\b",
            r"\b(is it a good)\b",
            r"\b(is it safe)\b",
            r"\b(good investment)\b",
            r"\b(better to invest)\b",
            r"\b(should i choose)\b",
            r"\b(which is better)\b",
            r"\b(is it worth it)\b",
            r"\b(recommend)\b",
            r"\b(recommendation)\b",
            r"\b(best fund)\b",
            r"\b(which fund to buy)\b",
            r"\b(which fund should i)\b",
            r"\b(will it go up)\b",
            r"\b(will it rise)\b",
            r"\b(will it fall)\b",
            r"\b(double my money)\b",
            r"\b(safe investment)\b",
            r"\b(safe to invest)\b",
            r"\b(predict)\b",
            r"\b(forecast)\b",
            r"\b(allocate my portfolio)\b",
            r"\b(portfolio allocation)\b",
            r"\b(diversify)\b",
            r"\b(ideal mix)\b",
            r"\b(optimal mix)\b",
            r"\b(create (a )?portfolio)\b",
            r"\b(build (a )?portfolio)\b",
            r"\b(how much (should|to) (invest|allocate))\b",
            r"\b(percentage (should|to) invest)\b",
            r"\b(outperform)\b",
            r"\b(underperform)\b",
            r"\b(beat the market)\b",
            r"\b(give (good|high|safe) returns)\b",
            r"\b(will (it|this|the fund).*(be good|be safe))\b",
        ]
        
        # PII detection patterns
        self.pii_patterns = [
            r"\b(pan is|pan number|pan:)\b",
            r"\b([a-z]{5}[0-9]{4}[a-z]{1})\b",  # PAN format
            r"\b(aadhaar is|aadhaar number|aadhaar:)\b",
            r"\b(\d{4}[ -]?\d{4}[ -]?\d{4})\b",  # Aadhaar-like pattern
            r"\b(phone|mobile|contact)\b.*\b(\d{10})\b",
            r"\b(email)\b.*\b(@)\b",
            r"\b(account number|acc no|customer id)\b",
            r"\b(otp|one time password)\b",
        ]
        
        # Personal/account query patterns
        self.personal_patterns = [
            r"\b(my balance|my holding|my account|my statement|my portfolio|my investment)\b",
            r"\b(my tax|my units|my nav|my redemption)\b",
            r"\b(check my|show my|view my|my hdfc)\b",
            r"\b(how much (do i have|did i invest|is my))\b",
        ]
        
        # Performance/return patterns
        self.performance_patterns = [
            r"\b(returns?|cagr|xirr|performance|perform)\b",
            r"\b(1-year|2-year|3-year|5-year|10-year|annualized)\b.*\b(return|growth)\b",
            r"\b(highest return|best return|top return)\b",
            r"\b(performance chart|performance graph|nav history)\b",
            r"\b(how (much|many).*(grow|increase|return))\b",
        ]
        
        # Comparison patterns
        self.comparison_patterns = [
            r"\b(which is better|which one is better|better than)\b",
            r"\b(compare|vs|versus)\b.*\b(and|with)\b",
            r"\b(lowest expense|highest return|best performer)\b",
            r"\b(difference between|difference in)\b",
        ]
        
        # Other AMC patterns
        self.other_amc_patterns = [
            r"\b(sbi|icici|axis|kotak|franklin|aditya birla|tata|uti|lic|nippon|idfc|bandhan|bank of india|canara robeco|dsp|hsbc|itgi|jm financial|mahindra|mirae|mohit|pgim|quant|sundaram|white oak|worldequi)\b.*\b(fund|mutual)\b",
            r"\b(sbi small cap|sbi large cap|sbi flexi cap|sbi hybrid)\b",
            r"\b(icici prudential|icici blue chip|icici technology)\b",
            r"\b(axis midcap|axis smallcap|axis bluechip)\b",
            r"\b(kotak flexicap|kotak emerging)\b",
            r"\b(franklin templeton|franklin india)\b",
        ]
        
    def check_query(self, query: str, context_fund: str = None) -> tuple[bool, str]:
        """
        Phase 4.1: Check if the user query violates constraints.
        Returns (is_safe: bool, violation_message: str)
        """
        lower_query = query.lower()

        # Priority 1: PII violations (highest priority)
        for pattern in self.pii_patterns:
            if re.search(pattern, lower_query):
                logging.warning("Input Guardrail triggered by PII pattern: %s", pattern)
                return False, (
                    "For your privacy and security, I cannot process queries containing "
                    "personally identifiable information such as PAN, Aadhaar, phone numbers, "
                    "or email addresses. Please remove such information and try again."
                )
        
        # Priority 2: Personal/account queries
        for pattern in self.personal_patterns:
            if re.search(pattern, lower_query):
                logging.warning("Input Guardrail triggered by personal query pattern: %s", pattern)
                return False, (
                    "I cannot access personal account information or account-specific details. "
                    "Please check your HDFC account directly or contact customer support."
                )
        
        # Priority 3: Advisory and recommendation patterns
        for pattern in self.advisory_patterns:
            if re.search(pattern, lower_query):
                logging.warning("Input Guardrail triggered by advisory pattern: %s", pattern)
                return False, (
                    "I am a factual assistant and cannot provide investment advice or "
                    "recommendations. Please consult a SEBI-registered financial advisor."
                )
        
        # Priority 4: Performance/return queries
        for pattern in self.performance_patterns:
            if re.search(pattern, lower_query):
                logging.warning("Input Guardrail triggered by performance pattern: %s", pattern)
                return False, (
                    "Performance data changes frequently and requires interpretation. "
                    "Please check the official HDFC factsheet for the latest performance information."
                )
        
        # Priority 5: Comparison queries
        for pattern in self.comparison_patterns:
            if re.search(pattern, lower_query):
                logging.warning("Input Guardrail triggered by comparison pattern: %s", pattern)
                return False, (
                    "Comparisons require subjective judgment and investment advice. "
                    "I can only provide factual information about individual HDFC funds."
                )
        
        # Priority 6: Other AMC funds
        for pattern in self.other_amc_patterns:
            if re.search(pattern, lower_query):
                logging.warning("Input Guardrail triggered by other AMC pattern: %s", pattern)
                return False, (
                    "I can only answer questions about HDFC mutual funds in my knowledge base. "
                    "Please specify an HDFC fund or check the official website of other AMCs."
                )

        # Priority 7: Off-topic queries
        if is_off_topic(query, context_fund):
            logging.warning("Off-topic query blocked.")
            return False, (
                "I can only answer factual questions about specific HDFC mutual funds "
                "in my knowledge base. " + _available_funds_hint()
            )

        return True, ""


class OutputGuard:
    def __init__(self):
        # Comprehensive banned phrases that the LLM shouldn't generate
        self.banned_phrases = [
            r"\b(i recommend)\b",
            r"\b(i would recommend)\b",
            r"\b(i suggest)\b",
            r"\b(you should invest)\b",
            r"\b(you should buy)\b",
            r"\b(you should choose)\b",
            r"\b(you must invest)\b",
            r"\b(guaranteed returns)\b",
            r"\b(guarantee)\b",
            r"\b(surefire way)\b",
            r"\b(sure shot)\b",
            r"\b(risk-free)\b",
            r"\b(buy this)\b",
            r"\b(buy this fund)\b",
            r"\b(highly recommended)\b",
            r"\b(best option)\b",
            r"\b(best choice)\b",
            r"\b(i advise)\b",
            r"\b(my advice)\b",
            r"\b(in my opinion)\b",
            r"\b(i think you should)\b",
            r"\b(it would be wise)\b",
            r"\b(i strongly suggest)\b",
        ]
        
        # Patterns for hallucination detection
        self.hallucination_patterns = [
            r"\b(i am not sure|i don't have information|i cannot find)\b.*\b(but|however)\b",
            r"\b(based on general knowledge)\b",
            r"\b(typically|generally|usually)\b.*\b(mutual funds)\b",
            r"\b(most funds|many funds)\b",
        ]

    def check_response(self, response: str) -> str:
        """
        Phase 4.2: Post-generation check for hallucinations or advice.
        If a banned phrase is found, override the response.
        """
        lower_resp = response.lower()
        
        # Check for advisory/recommendation phrases
        for pattern in self.banned_phrases:
            if re.search(pattern, lower_resp):
                logging.warning("Output Guardrail triggered by banned phrase: %s", pattern)
                return "The generated response was flagged by safety guardrails for potentially containing investment advice. As a factual assistant, I cannot provide this information."
        
        # Check for potential hallucinations
        for pattern in self.hallucination_patterns:
            if re.search(pattern, lower_resp):
                logging.warning("Output Guardrail triggered by hallucination pattern: %s", pattern)
                return "I do not have sufficient information in my knowledge base to answer this question accurately. Please check the official HDFC factsheet or contact customer support."
                
        return response
