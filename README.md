# FundQuest AI: Professional Mutual Fund FAQ Assistant

FundQuest AI is a production-grade, strictly factual RAG (Retrieval-Augmented Generation) assistant designed for mutual fund FAQs. It enforces strict compliance guardrails, returning concise, verifiable data without providing financial advice.

## 🏗 Architecture Overview

This project is built using a decoupled architecture, optimized for scalability and strict regulatory compliance.

- **Frontend (React/Vite & Tailwind CSS):** A high-fidelity, "Midnight Forest & Mint Teal" dark mode dashboard. Features structured "Analysis Core" cards for displaying qualitative data and quantitative metrics natively. Hosted on **Vercel**.
- **Backend (FastAPI):** A high-performance REST API handling query orchestration, guardrail validation, and structured JSON response generation. Hosted on **Railway**.
- **LLM Engine (Groq Llama-3.1-8b):** Provides lightning-fast response generation based strictly on the retrieved context. Zero temperature setting ensures deterministic, hallucination-free outputs.
- **Vector Database (ChromaDB):** Local vector embeddings using `BAAI/bge-small-en-v1.5`. 
- **CI/CD Data Refresh Pipeline:** A GitHub Action scheduled at 09:15 AM IST automatically runs web scraping, data extraction, chunking, and ChromaDB vector ingestion every day. This Git-backed approach triggers zero-downtime rolling updates on Railway.

## 📊 Monitored Mutual Funds

The knowledge base is continuously updated from the official Groww factsheets for the following HDFC Mutual Funds:
1. HDFC Mid-Cap Opportunities Fund
2. HDFC Equity Savings Fund
3. HDFC Focused 30 Fund
4. HDFC ELSS Tax Saver Fund
5. HDFC Top 100 Fund (Large Cap)

## 🛡️ Guardrails & Compliance (FACTS-ONLY MODE)

The system operates in a perpetual "Facts-Only" mode. 
1. **Input Guardrails:** Regex and keyword-based filtering block queries containing PII (PAN, Aadhaar, Account Numbers) and advisory language ("Should I buy?", "Is this a good investment?").
2. **Output Guardrails:** Ensures responses are limited to exactly 3 sentences, strictly derived from the context, and appended with a specific source citation and timestamp. It actively blocks comparative responses between funds.

## 🚀 Setup & Local Development

### Prerequisites
- Python 3.12+
- Node.js 18+
- A [Groq API Key](https://console.groq.com/)

### 1. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create a .env file and add your GROQ API key
echo "GROQ_API_KEY=your_api_key_here" > .env

# Run the FastAPI server (Runs on http://localhost:8000)
python -m src.api
```

### 2. Frontend Setup
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Vite development server (Runs on http://localhost:5173)
npm run dev
```

## ⚠️ Known Limitations
- **Data Source Dependency:** The system currently relies on the HTML structure of Groww mutual fund pages. Changes to their UI may require adjustments to the regex extraction patterns in `src/phase2_knowledge_base/extractor.py`.
- **Stateless Chat:** To comply with privacy requirements, the backend is strictly stateless and does not retain user conversation history across sessions.
- **Metric Extraction Constraints:** The regex currently only parses AUM, Expense Ratio, NAV, Minimum SIP, Exit Load, Benchmark, Risk, and Fund Manager. Additional metrics will require updated extraction rules.
