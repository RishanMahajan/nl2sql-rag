'''
this part will help us build the prompt that will be sent to the LLM.
it will consist of the context(relevant tables),user question and some
specific instructions.
'''

SYSTEM_PROMPT = """You are a MySQL expert. You convert English questions into MySQL queries.

Rules:
- Only use the tables and columns given in the schema context below.
- Only output the SQL query. No explanation, no markdown formatting, no ```sql fences.
- Use MySQL syntax.
- If the question cannot be answered with the given schema, output exactly: CANNOT_ANSWER
"""


def build_schema_context(schema_chunks):
    """Join retrieved schema chunks into a single context block."""
    return "\n".join(schema_chunks)


def build_prompt(question, schema_chunks, error=None, previous_sql=None):
    """
    Build the user-facing prompt from retrieved schema chunks + the question.
    If `error` and `previous_sql` are given, this becomes a retry prompt (Stage 6b)
    that asks the LLM to fix its previous attempt.
    """
    context = build_schema_context(schema_chunks)

    if error is None:
        return f"""Schema:
{context}

Question: {question}

SQL query:"""

    return f"""Schema:
{context}

Question: {question}

Your previous attempt:
{previous_sql}

That query failed with this error:
{error}

Fix the query using only the schema above.

SQL query:"""


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from retrieval.vector_store import query_schema

    question = "How many films are longer than 2 hours?"
    chunks = query_schema(question)
    prompt = build_prompt(question, chunks)

    print("--- SYSTEM PROMPT ---")
    print(SYSTEM_PROMPT)
    print("\n--- USER PROMPT ---")
    print(prompt)
