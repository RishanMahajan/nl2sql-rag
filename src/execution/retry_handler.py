import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.vector_store import query_schema
from retrieval.embed_schema import fetch_table_schemas
from generation.prompt_builder import SYSTEM_PROMPT, build_prompt
from generation.llm_client import generate_sql
from validation.sql_validator import validate


def generate_valid_sql(question, max_attempts=3, top_k=3):
    """
    Generate SQL for a question, validating each attempt. If validation fails,
    the error is fed back to the LLM so it can fix its own mistake.
    Returns (sql, None) on success or (None, last_error) after exhausting attempts.
    """
    schema_chunks = query_schema(question, top_k=top_k)
    known_tables = fetch_table_schemas().keys()

    sql = None
    error = None

    for attempt in range(1, max_attempts + 1):
        if attempt == 1:
            prompt = build_prompt(question, schema_chunks)
        else:
            prompt = build_prompt(question, schema_chunks, error=error, previous_sql=sql)

        sql = generate_sql(SYSTEM_PROMPT, prompt)
        is_valid, error = validate(sql, known_tables)

        if is_valid:
            return sql, None

        print(f"Attempt {attempt}/{max_attempts} failed: {error}")

    return None, error


if __name__ == "__main__":
    question = "How many films are longer than 2 hours?"
    sql, error = generate_valid_sql(question)

    if sql:
        print(f"\nQuestion: {question}")
        print(f"Valid SQL: {sql}")
    else:
        print(f"\nCould not produce valid SQL after retries. Last error: {error}")
