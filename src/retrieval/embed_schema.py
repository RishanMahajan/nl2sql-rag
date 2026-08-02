"""

https://chatgpt.com/share/6a6f7e5e-a760-83ee-853c-2fe292685601

This file is a schema extractor. Its only job is to read your MySQL 
database structure and convert it into text that an LLM can understand.

In an NL2SQL RAG Agent, the LLM doesn't know your database schema 
beforehand. So before it can generate SQL queries, you need to tell 
things like:
What tables exist?
What columns does each table have?
What are the data types?

Later, these text chunks will be embedded into vectors and stored in a 
vector database like chroma db.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.db_connector import get_connection


def fetch_table_schemas():
    """Query INFORMATION_SCHEMA for every table + its columns in the current database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        ORDER BY TABLE_NAME, ORDINAL_POSITION;
    """) 
    rows = cursor.fetchall()
    '''
    This SQL is querying a special database called INFORMATION_SCHEMA.

    This database is built into MySQL and stores metadata about all 
    databases.
    '''

    cursor.close()
    conn.close()

    tables = {}
    for table_name, column_name, data_type in rows:
        tables.setdefault(table_name, []).append((column_name, data_type))

    return tables


def build_schema_chunks(tables):
    """Turn {table_name: [(column, type), ...]} into one text chunk per table."""
    chunks = []
    for table_name, columns in tables.items():
        column_str = ", ".join(f"{col} ({dtype})" for col, dtype in columns)
        text = f"Table: {table_name}. Columns: {column_str}."
        chunks.append({"table_name": table_name, "text": text})
    return chunks

# refer chatgpt chat for proper visualisation

if __name__ == "__main__":
    tables = fetch_table_schemas()
    chunks = build_schema_chunks(tables)
    for chunk in chunks:
        print(chunk["text"])
