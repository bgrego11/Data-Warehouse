# //script to scrape for crypto prices
from typing import Optional
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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

    except Exception:
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
    price_text = fetch_span_text(url, selector)
    if price_text is None:
        raise ValueError("Could not find the BTC price on the page.")

    timestamp = datetime.now()
    df = build_df(timestamp, price_text, ccy, url)
    return df
# collates data from all urls and selectors into a single df
def collate():
    all_dfs = []
    for item in selector_dict:
        df = ingest(item['url'], item['selector'], item['ccy'], item['url'])
        all_dfs.append(df)
    final_df = pd.concat(all_dfs, ignore_index=True)
    return final_df

# placeholder for db upload function and logging

if __name__ == "__main__":
    # Set pandas display options to show full dataframe
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    df = collate()
    print(df)
