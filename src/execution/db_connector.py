import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
    )

def test_connection():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print(f"Connected successfully. Found {len(tables)} tables:")
    for t in tables:
        print(f"  - {t[0]}")

    cursor.execute("SELECT COUNT(*) FROM film;")
    film_count = cursor.fetchone()[0]
    print(f"\nfilm table row count: {film_count}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_connection()