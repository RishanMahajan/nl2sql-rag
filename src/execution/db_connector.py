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

def execute_query(sql):
    """Run a validated SELECT query and return rows as a list of dicts (column_name -> value)."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


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

"""
so this is what ive understood -: 
load_dotenv() just looks for the .env file and gets all the environment 
variables from it because we cant hard code them as then we'll be pushing
sensitive info to git the get connection func is just creating an object
that contains all environment variables in the test connection the conn
variable just holds the object created above. and then we initialise a 
cursor with that object as python and mysql cant communicate directly 
but only through a cursor. now any sql query we run will be in the form 
cursor.execute(query;) now the fetchall() gets the rows returned by the 
last query and converts these tuples into a list of tuples so that we 
can calculate its length and iterate over them easily as well and then 
rest of the code is actually simple


On get_connection() — it's not quite "creating an object that contains 
all environment variables." It's actually opening a live network 
connection to the MySQL server, using those environment variables as the
login credentials. The object it returns (conn) represents that active 
connection itself.


The conn is the open connection/session; the cursor is the object you 
actually use to send queries and pull results through that connection.
You could have multiple cursors on the same connection running different 
queries — the cursor is your "query executor," the connection is your
"pipe to the database."
"""    