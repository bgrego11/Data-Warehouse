
from sqlalchemy import create_engine
import logging


def load_data_to_db(dataframe, table_name, db_url):
    """
    Load a pandas DataFrame into a SQL database table.

    Parameters:
    - dataframe: pd.DataFrame - The DataFrame to load into the database.
    - table_name: str - The name of the target table in the database.
    - db_url: str - The database connection URL.

    Returns:
    None
    """
    # Create a database engine
    engine = create_engine(db_url)
    logging.info(f"Database engine created for URL: {db_url}")

    # Load the DataFrame into the specified table
    with engine.connect() as connection:
        dataframe.to_sql(table_name, con=connection, if_exists='append', index=False)
        logging.info(f"Data loaded into table '{table_name}' successfully.")
