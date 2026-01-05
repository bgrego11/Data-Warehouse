import pandas as pd
import logging
from db_loader import load_data_to_db
import os

def clean_history_data(file_path, ccy, source):
    """
    Clean historical data from a CSV file.

    Parameters:
    - file_path: str - The path to the CSV file containing historical data.

    Returns:
    - pd.DataFrame - The cleaned DataFrame.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)
    logging.info(f"Historical data loaded from {file_path}")

    # Example cleaning steps
    # Drop duplicates
    df.drop_duplicates(inplace=True)
    logging.info("Duplicates dropped from historical data")

    # Handle missing values (example: fill with mean for numeric columns)
    for column in df.select_dtypes(include=['number']).columns:
        mean_value = df[column].mean()
        df[column].fillna(mean_value, inplace=True)
        logging.info(f"Missing values in column '{column}' filled with mean: {mean_value}")

    # Convert date columns to datetime format (example)
    for column in df.select_dtypes(include=['object']).columns:
        if 'date' in column.lower():
            df[column] = pd.to_datetime(df[column], errors='coerce')
            logging.info(f"Column '{column}' converted to datetime format")
    # rename columns to match database schema
    df.rename(columns={'Start': 'timestamp',
                       'Close': 'price'}, inplace=True)
    df['currency'] = ccy
    df['source'] = source
    logging.info(f"Added 'currency' column with value: {ccy}")
    logging.info(f"Added 'source' column with value: {source}")
    #select only columns needed for database
    df = df[['timestamp', 'price', 'currency', 'source']]

    return df
def process_and_load_history(file_path, ccy, source, table_name):
    """
    Process historical data from a CSV file and load it into a database.

    Parameters:
    - file_path: str - The path to the CSV file containing historical data.
    - ccy: str - The currency code to add to the data.
    - source: str - The source identifier to add to the data.
    - table_name: str - The name of the target table in the database.
    - db_url: str - The database connection URL.

    Returns:
    None
    """
    # Clean the historical data
    cleaned_data = clean_history_data(file_path, ccy, source)
    logging.info("Historical data cleaned successfully")
    # Load the cleaned data into the database
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    
    if all([db_host, db_port, db_name, db_user, db_password]):
        db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        logging.info("Loading data to database...")
        load_data_to_db(cleaned_data, table_name, db_url)

    
    
    logging.info("Cleaned historical data loaded into database successfully")

#load data
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    #  parameters
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Historic Data/solana_2020-04-09_2026-01-02.csv')
    ccy = 'SOL'
    source = 'https://coincodex.com/crypto/solana/historical-data/'
    table_name = 'crypto_prices'
    process_and_load_history(file_path, ccy, source, table_name)