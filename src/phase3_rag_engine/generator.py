"""Phase 3.3 and 3.4: LLM Prompting and Response Generation."""
import os
import logging
from groq import Groq
from dotenv import load_dotenv
from src.phase3_rag_engine.retriever import FactRetriever
from src.phase4_guardrails.guardrails import InputGuard, OutputGuard

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Local dev: load .env if present. Railway/Vercel inject vars via the platform.
load_dotenv()
if not os.environ.get("GROQ_API_KEY"):
    logging.warning(
        "GROQ_API_KEY is not set. Add it to .env locally or to Railway service variables."
    )

class RAGGenerator:
    def __init__(self, retriever=None, model="llama-3.1-8b-instant"):
        self.retriever = retriever or FactRetriever()
        self.model = model
        self.input_guard = InputGuard()
        self.output_guard = OutputGuard()
        
        # Initialize Groq client
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logging.warning(f"GROQ_API_KEY is None! Current keys: {list(os.environ.keys())[:10]}...")
        
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def construct_prompt(self, query: str, context_chunks: list) -> str:
        """Phase 3.3: Construct a strict prompt using the retrieved context."""
        
        context_text = "\n".join([f"- {chunk['text']}" for chunk in context_chunks])
        
        system_prompt = f"""You are a highly restricted, factual Mutual Fund FAQ assistant.
Your strict instructions:
1. Answer the user's question ONLY using the provided Context.
2. If the answer is not contained in the Context, you must reply: "I do not have the information to answer that."
3. Keep your response concise (maximum 3 sentences).
4. Maintain a neutral, factual tone. DO NOT give investment advice or opinions.

Context:
{context_text}
"""
        return system_prompt

    def generate_response(self, query: str) -> str:
        """Phase 3.4: Generate response via Groq and append citation footer."""
        
        # Phase 4.1: Input Guardrail Check
        is_safe, msg = self.input_guard.check_query(query)
        if not is_safe:
            return msg
            
        if not self.client:
            return "Error: GROQ_API_KEY is not configured."
            
        logging.info(f"Retrieving context for query: '{query}'")
        chunks = self.retriever.retrieve_context(query)
        
        if not chunks:
            return "I do not have the information to answer that."
            
        system_prompt = self.construct_prompt(query, chunks)
        
        logging.info("Generating response via Groq API...")
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                model=self.model,
                temperature=0.0, # Zero temperature for factual consistency
            )
            
            raw_response = chat_completion.choices[0].message.content.strip()
            
            # Phase 4.2: Output Guardrail Check
            safe_response = self.output_guard.check_response(raw_response)
            if "flagged by safety guardrails" in safe_response:
                return safe_response
            
            # Format Footer (Phase 3.4)
            # Use the first chunk's metadata for the primary citation
            primary_meta = chunks[0]['metadata']
            date = primary_meta.get("last_updated", "Unknown Date").split("T")[0]
            url = primary_meta.get("source_url", "#")
            fund_name = primary_meta.get("fund_name", "Source")
            
            footer = f"\n\n*Last updated from sources: {date} | [{fund_name}]({url})*"
            
            return safe_response + footer
            
        except Exception as e:
            logging.error(f"Error during generation: {e}")
            return f"An error occurred while generating the response: {e}"

    def generate_structured_response(self, query: str) -> dict:
        """Phase 5.1: Generate a structured JSON response for the API."""
        
        # Guardrail Check
        is_safe, msg = self.input_guard.check_query(query)
        if not is_safe:
            return {
                "answer": msg,
                "metrics": {},
                "source": None,
                "status": "blocked"
            }
            
        if not self.client:
            return {"error": "GROQ_API_KEY not set"}
            
        chunks = self.retriever.retrieve_context(query)
        if not chunks:
            return {
                "answer": "I do not have the information to answer that.",
                "metrics": {},
                "source": None,
                "status": "no_context"
            }
            
        context_text = "\n".join([f"- {chunk['text']}" for chunk in chunks])
        
        # Prompt for JSON
        json_prompt = f"""You are a highly restricted, factual Mutual Fund FAQ assistant.
Answer the user's question ONLY using the provided Context.
Keep the answer concise (max 2 sentences).
Also extract key metrics like Expense Ratio, Exit Load, or NAV if present in the context.

Context:
{context_text}

Return your response in EXACTLY this JSON format:
{{
  "answer": "Your factual answer here.",
  "metrics": {{
    "Expense Ratio": "val",
    "Exit Load": "val",
    "NAV": "val"
  }}
}}
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": json_prompt},
                    {"role": "user", "content": query}
                ],
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(chat_completion.choices[0].message.content)
            
            # Post-generation Output Guardrail
            result["answer"] = self.output_guard.check_response(result["answer"])
            
            # Add metadata
            primary_meta = chunks[0]['metadata']
            result["source"] = {
                "fund_name": primary_meta.get("fund_name"),
                "url": primary_meta.get("source_url"),
                "last_updated": primary_meta.get("last_updated", "").split("T")[0]
            }
            result["status"] = "success"
            
            return result
            
        except Exception as e:
            logging.error(f"Error in structured generation: {e}")
            return {
                "answer": f"Error: {e}",
                "metrics": {},
                "source": None,
                "status": "error"
            }

if __name__ == "__main__":
    # Note: Requires GROQ_API_KEY environment variable
    generator = RAGGenerator()
    query = "What is the expense ratio of HDFC Mid-Cap Fund?"
    response = generator.generate_response(query)
    print(f"\nQuery: {query}")
    print("-" * 20)
    print(response.encode('utf-8', 'replace').decode('utf-8'))
