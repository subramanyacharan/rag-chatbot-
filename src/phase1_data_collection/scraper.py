"""Scraper for Mutual Fund factsheets."""
import os
import json
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup

from .config import TARGET_URLS, DATA_RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FundScraper:
    def __init__(self, urls, output_dir):
        self.urls = urls
        self.output_dir = output_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def fetch_page(self, url):
        """Fetch the HTML content of the URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch {url}: {e}")
            return None

    def extract_text(self, html):
        """Extract readable text from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text and clean it
        text = soup.get_text(separator=' ', strip=True)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    def run(self):
        """Run the scraper on all configured URLs."""
        for url in self.urls:
            logging.info(f"Scraping {url}...")
            html = self.fetch_page(url)
            
            if html:
                text_content = self.extract_text(html)
                fund_name_slug = url.split('/')[-1]
                
                data = {
                    "url": url,
                    "last_updated": datetime.now().isoformat(),
                    "raw_text": text_content
                }
                
                file_path = os.path.join(self.output_dir, f"{fund_name_slug}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                logging.info(f"Saved data to {file_path}")

if __name__ == "__main__":
    scraper = FundScraper(TARGET_URLS, DATA_RAW_DIR)
    scraper.run()
