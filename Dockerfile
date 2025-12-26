# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Chromium and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY Ingestion/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY Ingestion/ ./Ingestion/

# Set the working directory to Ingestion
WORKDIR /app/Ingestion

# Run the scraper
CMD ["python", "price_scraper.py"]
