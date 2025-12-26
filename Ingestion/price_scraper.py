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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


# ============================================================================
# CONFIGURATION
# ============================================================================

CRYPTOCURRENCIES = [
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

WEBDRIVER_OPTIONS = [
    "--headless=new",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-software-rasterizer"
]


# ============================================================================
# LOGGING SETUP
# ============================================================================

def configure_logging() -> None:
    """Set up logging to both console and rotating log file for tracking scraper activity."""
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'scraper_{datetime.now().strftime("%Y%m%d")}.log'
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler with rotation (5MB max, keep 10 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )
    
    # Suppress verbose third-party logging
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('WDM').setLevel(logging.WARNING)


# ============================================================================
# WEBDRIVER MANAGEMENT
# ============================================================================

def get_driver_options() -> Options:
    """Set up browser options for headless scraping (no visible window)."""
    options = Options()
    for arg in WEBDRIVER_OPTIONS:
        options.add_argument(arg)
    return options


def get_chromium_driver(options: Options) -> webdriver.Chrome:
    """Initialize WebDriver using system Chromium in Docker or downloaded driver locally. Had issues switching from AMD to Apple chip"""
    if os.path.exists('/.dockerenv'):
        service = Service('/usr/bin/chromedriver')
        return webdriver.Chrome(service=service, options=options)
    else:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)


# ============================================================================
# WEB SCRAPING
# ============================================================================

# let page load -> let page update -> grab price

def wait_for_element(driver: webdriver.Chrome, css_selector: str, timeout: int = 10) -> None:
    """Block execution until the target element appears on the page to handle slow-loading content"""
    logging.debug(f"Waiting for element '{css_selector}' (timeout: {timeout}s)...")
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )
    logging.debug(f"Element found: '{css_selector}'")


def wait_for_dynamic_update(driver: webdriver.Chrome, css_selector: str, 
                           initial_text: str, timeout: int = 5, poll_frequency: float = 0.5) -> None:
    """Wait for JavaScript to finish updating the price to prevent stale/loading text"""
    logging.debug(f"Waiting for price update (initial: '{initial_text}', timeout: {timeout}s)...")
    def text_updated(drv):
        try:
            cur = drv.find_element(By.CSS_SELECTOR, css_selector).text.strip()
        except Exception:
            return False
        if initial_text == "":
            return cur != ""
        return cur != initial_text
    
    WebDriverWait(driver, timeout, poll_frequency).until(text_updated)
    logging.debug("Price update detected")


def extract_text(driver: webdriver.Chrome, css_selector: str) -> str:
    """Pull text content from HTML element."""
    logging.debug(f"Extracting text from '{css_selector}'...")
    element = driver.find_element(By.CSS_SELECTOR, css_selector)
    text = element.text.strip()
    logging.debug(f"Extracted: '{text}'")
    return text


def fetch_span_text(url: str, css_selector: str, timeout: int = 10, 
                   text_timeout: int = 5, poll_frequency: float = 0.5) -> str:
    """hit the url grab initial price wait for it to be stale and grab the updated price"""
    logging.debug(f"Starting scrape for {url}")
    options = get_driver_options()
    driver = get_chromium_driver(options)
    
    try:
        logging.debug(f"Loading URL: {url}")
        driver.get(url)
        logging.debug(f"Page loaded successfully")
        
        try:
            wait_for_element(driver, css_selector, timeout)
        except TimeoutException:
            raise ValueError(f"CSS selector '{css_selector}' not found on page - check selector or page structure")
        
        try:
            initial_text = extract_text(driver, css_selector)
        except NoSuchElementException:
            raise ValueError(f"Element disappeared after initial load - page may be broken")
        
        try:
            wait_for_dynamic_update(driver, css_selector, initial_text, text_timeout, poll_frequency)
        except TimeoutException:
            raise ValueError(f"Price did not update after {text_timeout}s - selector may be wrong or price is static")
        
        final_text = extract_text(driver, css_selector)
        logging.debug(f"Scrape complete: '{final_text}'")
        return final_text
    
    except WebDriverException as e:
        raise ValueError(f"Browser/WebDriver error: {str(e)} - check if URL is valid")
    finally:
        driver.quit()


# ============================================================================
# DATA PROCESSING
# ============================================================================

def clean_price(price_str: str) -> float:
    """Remove currency symbols and commas, then convert to a number we can store."""
    cleaned = price_str.replace('$', '').replace(',', '')
    return float(cleaned)


def build_df(timestamp: datetime, price: str, ccy: str, source: str) -> pd.DataFrame:
    """Package scraped data into a DataFrame row (timestamp, cleaned price, currency, source URL)."""
    price_float = clean_price(price)
    return pd.DataFrame({
        'Timestamp': [timestamp],
        'Price': [price_float],
        'Currency': [ccy],
        'Source': [source]
    })


def ingest(url: str, selector: str, ccy: str, source: str) -> pd.DataFrame:
    """Scrape price from a single cryptocurrency page and return it as a DataFrame."""
    logging.info(f"Scraping {ccy} price...")
    price_text = fetch_span_text(url, selector)
    
    timestamp = datetime.now()
    df = build_df(timestamp, price_text, ccy, source)
    logging.info(f"Successfully scraped {ccy}: {price_text}")
    return df


def collate() -> pd.DataFrame:
    """Scrape all configured cryptocurrencies and combine results into one DataFrame."""
    logging.info(f"Starting data collection for {len(CRYPTOCURRENCIES)} cryptocurrencies")
    
    all_dfs = []
    successful = 0
    failed = 0
    
    for item in CRYPTOCURRENCIES:
        try:
            df = ingest(item['url'], item['selector'], item['ccy'], item['url'])
            all_dfs.append(df)
            successful += 1
        except Exception as e:
            logging.error(f"Failed to process {item['ccy']}: {str(e)}")
            failed += 1
    
    if not all_dfs:
        raise ValueError("Failed to collect any price data")
    
    final_df = pd.concat(all_dfs, ignore_index=True)
    logging.info(f"Data collection complete: {successful} successful, {failed} failed")
    logging.info(f"Total records collected: {len(final_df)}")
    return final_df


# ============================================================================
# DISPLAY UTILITIES
# ============================================================================

def configure_pandas_display() -> None:
    """Show full DataFrame output without truncation (for debugging)."""
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)


def display_results(df: pd.DataFrame) -> None:
    """Pretty-print the scraped data to console."""
    print("\n" + "=" * 50)
    print("SCRAPED DATA:")
    print("=" * 50)
    print(df)
    print("=" * 50 + "\n")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    configure_logging()
    configure_pandas_display()
    
    logging.info("=" * 50)
    logging.info("Crypto Price Scraper Started")
    logging.info("=" * 50)
    
    try:
        df = collate()
        display_results(df)
        logging.info("Script completed successfully")
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        raise
