# //script to scrape for crypto prices
from typing import Optional
import pandas as pd
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Configure logging to monitor the scraping process
log_file = log_dir / f'scraper_{datetime.now().strftime("%Y%m%d")}.log'

# Create formatters and handlers
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console handler - show logs in terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# File handler with rotation (5MB max, keep 10 backups)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=10
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

# Suppress verbose logging from third-party libraries related to chrome driver versions to keep logs clean
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.WARNING)


# running list of urls and selectors to scrape
selector_dict = [
    {
    "ccy": "BTC",
    "url": "https://coinmarketcap.com/currencies/bitcoin/",
    "selector": "span.sc-65e7f566-0.WXGwg.base-text"
},
    {
    "ccy": "ETH",
    "url": "https://coinmarketcap.com/currencies/ethereum/",
    "selector": "span.sc-65e7f566-0.WXGwg.base-text"
},
{
    "ccy": "SOL",
    "url": "https://coinmarketcap.com/currencies/solana/",
    "selector": "span.sc-65e7f566-0.WXGwg.base-text"
}
]


# function to fetch price from url
def fetch_span_text( url: str,css_selector: str, timeout: int = 10, headless: bool = True, text_timeout: int = 5, poll_frequency: float = 0.5,) -> Optional[str]:
    logging.debug(f"Fetching data from URL: {url}")
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)

        # wait for the element to exist on the page
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )

        initial_text = el.text.strip()

        # waiting until the text updates as the page uses dynamic loading
        def text_updated(drv):
            try:
                cur = drv.find_element(By.CSS_SELECTOR, css_selector).text.strip()
            except Exception:
                return False
            if initial_text == "":
                return cur != ""
            return cur != initial_text

        try:
            WebDriverWait(driver, text_timeout, poll_frequency).until(text_updated)
        except TimeoutException:
            # timed out waiting for text update; return whatever we have (or None)
            final = driver.find_element(By.CSS_SELECTOR, css_selector).text.strip()
            return final or None

        final = driver.find_element(By.CSS_SELECTOR, css_selector).text.strip()
        return final or None

    except Exception as e:
        logging.error(f"Error fetching data from {url}: {str(e)}")
        return None
    finally:
        driver.quit()

# builds the df from the fetched price and current timestamp
def build_df(timestamp: datetime, price: str, ccy: str, source: str) -> pd.DataFrame:
    clean_price = price.replace('$', '').replace(',', '')
    price = float(clean_price)
    data = {'Timestamp': [timestamp], 'Price': [price], 'Currency': [ccy], 'Source': [source]}
    df = pd.DataFrame(data)
    return df
# collects the data for a single url and selector
def ingest(url: str, selector: str, ccy: str, source: str) -> pd.DataFrame:
    logging.info(f"Scraping {ccy} price...")
    price_text = fetch_span_text(url, selector)
    if price_text is None:
        logging.error(f"Failed to fetch price for {ccy}")
        raise ValueError(f"Could not find the {ccy} price on the page.")

    timestamp = datetime.now()
    df = build_df(timestamp, price_text, ccy, url)
    logging.info(f"Successfully scraped {ccy}: {price_text}")
    return df
# collates data from all urls and selectors into a single df
def collate():
    logging.info(f"Starting data collection for {len(selector_dict)} cryptocurrencies")
    all_dfs = []
    successful = 0
    failed = 0
    
    for item in selector_dict:
        try:
            df = ingest(item['url'], item['selector'], item['ccy'], item['url'])
            all_dfs.append(df)
            successful += 1
        except Exception as e:
            logging.error(f"Failed to process {item['ccy']}: {str(e)}")
            failed += 1
    
    if not all_dfs:
        logging.error("No data collected - all scrapes failed")
        raise ValueError("Failed to collect any price data")
    
    final_df = pd.concat(all_dfs, ignore_index=True)
    logging.info(f"Data collection complete: {successful} successful, {failed} failed")
    logging.info(f"Total records collected: {len(final_df)}")
    return final_df

# placeholder for db upload function and logging

if __name__ == "__main__":
    logging.info("=" * 50)
    logging.info("Crypto Price Scraper Started")
    logging.info("=" * 50)
    
    # Set pandas display options to show full dataframe
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    try:
        df = collate()
        print("\n" + "=" * 50)
        print("SCRAPED DATA:")
        print("=" * 50)
        print(df)
        print("=" * 50 + "\n")
        logging.info("Script completed successfully")
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        raise
