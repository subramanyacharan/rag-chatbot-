"""Extractor to parse factual data from raw mutual fund text."""
import os
import json
import re
import logging

from src.phase2_knowledge_base.fund_registry import fund_from_slug

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FactExtractor:
    def __init__(self, raw_dir, processed_dir):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        
        if not os.path.exists(self.processed_dir):
            os.makedirs(self.processed_dir)

    def extract_facts(self, text):
        """Extract key factual metrics from the raw text using regex."""
        facts = {}
        
        # Fund size (AUM)
        aum_match = re.search(r"Fund size \(AUM\)\s*₹([\d,.]+\s*Cr)", text)
        if aum_match:
            facts['aum'] = f"₹{aum_match.group(1).strip()}"
            
        # Expense Ratio
        er_match = re.search(r"Expense ratio\s*([\d.]+\s*%)", text)
        if er_match:
            facts['expense_ratio'] = er_match.group(1).strip()
            
        # NAV
        nav_match = re.search(r"NAV[: ]*.*?₹([\d,.]+)", text)
        if nav_match:
            facts['nav'] = f"₹{nav_match.group(1).strip()}"
            
        # Min SIP
        sip_match = re.search(r"Min\. for SIP\s*₹([\d,.]+)", text)
        if sip_match:
            facts['min_sip'] = f"₹{sip_match.group(1).strip()}"
            
        # Benchmark
        benchmark_match = re.search(r"Fund benchmark\s*(.*?)\s*Scheme Information", text)
        if benchmark_match:
            facts['benchmark'] = benchmark_match.group(1).strip()
            
        # Exit Load — first policy sentence only (avoid historical table noise)
        exit_load_match = re.search(
            r"(Exit load of \d+(?:\.\d+)?%[^.]*\.)", text, re.IGNORECASE
        )
        if exit_load_match:
            facts["exit_load"] = exit_load_match.group(1).strip()
            
        # Fund Manager 
        fm_match = re.search(r"([^.]+) is the Current Fund Manager", text)
        if fm_match:
            facts['fund_manager'] = fm_match.group(1).strip()
            
        # Riskometer
        risk_match = re.search(r"is rated (.*? risk)", text)
        if risk_match:
            facts['risk'] = risk_match.group(1).strip()
            
        return facts

    def generate_sentences(self, fund_name, facts):
        """Convert extracted facts into declarative sentences for the vector DB."""
        sentences = []
        if 'expense_ratio' in facts:
            sentences.append(f"The expense ratio of {fund_name} is {facts['expense_ratio']}.")
        if 'exit_load' in facts:
            sentences.append(f"The exit load for {fund_name} is: {facts['exit_load']}")
        if 'min_sip' in facts:
            sentences.append(f"The minimum SIP investment amount for {fund_name} is {facts['min_sip']}.")
        if 'aum' in facts:
            sentences.append(f"The total fund size or AUM of {fund_name} is {facts['aum']}.")
        if 'nav' in facts:
            sentences.append(f"The latest NAV of {fund_name} is {facts['nav']}.")
        if 'benchmark' in facts:
            sentences.append(f"The benchmark index for {fund_name} is the {facts['benchmark']}.")
        if 'risk' in facts:
            sentences.append(f"The riskometer rating for {fund_name} is {facts['risk']}.")
        if 'fund_manager' in facts:
            sentences.append(f"The current fund manager of {fund_name} is {facts['fund_manager']}.")
            
        return " ".join(sentences)

    def process_files(self):
        """Read raw JSONs, extract facts, and save processed JSONs."""
        for filename in os.listdir(self.raw_dir):
            if not filename.endswith('.json'):
                continue
                
            raw_path = os.path.join(self.raw_dir, filename)
            processed_path = os.path.join(self.processed_dir, filename)
            
            with open(raw_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            text = data.get("raw_text", "")
            
            # Derive fund name from URL or text
            fund_slug = filename.replace(".json", "")
            registry_entry = fund_from_slug(fund_slug)
            fund_name = (
                registry_entry["fund_name"]
                if registry_entry
                else fund_slug.replace("-", " ").title()
            )

            facts = self.extract_facts(text)
            clean_text = self.generate_sentences(fund_name, facts)
            
            # Save the processed data
            processed_data = {
                "fund_slug": fund_slug,
                "fund_name": fund_name,
                "url": data.get("url") or (registry_entry["url"] if registry_entry else ""),
                "last_updated": data.get("last_updated"),
                "extracted_facts": facts,
                "processed_text": clean_text,
            }
            
            with open(processed_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=4)
                
            logging.info(f"Processed {filename}: Found {len(facts)} facts.")

if __name__ == "__main__":
    extractor = FactExtractor("data/raw", "data/processed")
    extractor.process_files()
