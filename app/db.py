# server_flask/app/db.py

import os
import psycopg2
from dotenv import load_dotenv

# Load env variables for the db connection
load_dotenv()

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None