import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "fundoo_notes"),
}


def ensure_database():
    config = {key: value for key, value in DB_CONFIG.items() if key != "database"}
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    cursor.close()
    connection.close()


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def get_db():
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()
