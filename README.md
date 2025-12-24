# Crypto Scraper

A Python script that scrapes BCrypto price data from CoinMarketCap using Selenium.

## Prerequisites

### 1. Install Python

If you don't have Python installed on your machine, download it from [python.org](https://www.python.org/downloads/).

**Windows Installation Steps:**
1. Download the Python installer (3.8 or higher recommended)
2. Run the installer
3. **IMPORTANT:** Check the box "Add Python to PATH" during installation
4. Click "Install Now"
5. Verify installation by opening PowerShell and running:
   ```powershell
   python --version
   ```

### 2. Install Google Chrome

Selenium requires Chrome to be installed. Download it from [google.com/chrome](https://www.google.com/chrome/).

## Setup

### 1. Navigate to the Project Directory

```powershell
cd "Your Local Path\Data Warehouse\Ingestion"
```

### 2. Create a Virtual Environment

```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment

```powershell
. .\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` appear in your PowerShell prompt, indicating the virtual environment is active.

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

Or, if you don't have `requirements.txt`, install manually:

```powershell
pip install selenium webdriver-manager pandas
```

## Running the Script

Once the virtual environment is activated, run:

```powershell
python .\BTC_Scraper.py
```

The script will scrape the current BTC price from CoinMarketCap and display it.

## Deactivating the Virtual Environment

When you're done, deactivate the virtual environment:

```powershell
deactivate
```

## Troubleshooting

- **"python" is not recognized**: Make sure Python is in your PATH. Reinstall Python and check "Add Python to PATH" during setup.
- **Chrome driver issues**: Ensure Google Chrome is installed on your machine.
- **Module not found errors**: Make sure the virtual environment is activated and all dependencies are installed with `pip install -r requirements.txt`.
