# Crypto Scraper

A Python script that scrapes crypto price data from CoinMarketCap using Selenium.

## Prerequisites

### Docker (Recommended)

- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Ensure Docker is running before executing commands

### Local Development (Alternative)

<details>
<summary>Click to expand local setup instructions</summary>

#### 1. Install Python

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

#### 2. Install Google Chrome

Selenium requires Chrome to be installed. Download it from [google.com/chrome](https://www.google.com/chrome/).

</details>

## Running with Docker (Recommended)

### 1. Navigate to the Project Directory

```powershell
cd "C:\Users\YourUsername\Code Projects\Data Warehouse"
```

### 2. Build the Docker Image

```powershell
docker-compose build
```

### 3. Run the Scraper

```powershell
docker-compose up
```

The script will scrape crypto prices from CoinMarketCap and display the results in the terminal.

### Alternative: Run with Docker Directly

```powershell
docker build -t crypto-scraper .
docker run --rm crypto-scraper
```

## Running Locally (Without Docker)

<details>
<summary>Click to expand local development instructions</summary>

### 1. Navigate to the Ingestion Directory

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

### 5. Run the Script

```powershell
python price_scraper.py
```

### 6. Deactivate the Virtual Environment

When you're done, deactivate the virtual environment:

```powershell
deactivate
```

</details>

## Troubleshooting

### Docker Issues
- **Docker daemon not running**: Start Docker Desktop and wait for it to fully initialize
- **Build fails**: Try `docker-compose build --no-cache` to rebuild from scratch
- **Container exits immediately**: Check logs with `docker-compose logs`

### Local Development Issues
- **"python" is not recognized**: Make sure Python is in your PATH. Reinstall Python and check "Add Python to PATH" during setup.
- **Chrome driver issues**: Ensure Google Chrome is installed on your machine.
- **Module not found errors**: Make sure the virtual environment is activated and all dependencies are installed with `pip install -r requirements.txt`.
