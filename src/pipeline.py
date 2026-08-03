from execution.retry_handler import generate_valid_sql
from execution.db_connector import execute_query
from generation.llm_client import generate_answer


def answer_question(question):
    """
    Run the full NL2SQL pipeline for one question:
    retrieve schema -> generate SQL -> validate (with retries) -> execute -> summarize.
    Returns the SQL used and the final plain-English answer (or the failure reason).
    """
    sql, error = generate_valid_sql(question)

    if sql is None:
        return {
            "question": question,
            "sql": None,
            "answer": f"Sorry, I couldn't generate a valid query for that. ({error})",
        }

    rows = execute_query(sql)
    answer = generate_answer(question, rows)

    return {"question": question, "sql": sql, "answer": answer}


if __name__ == "__main__":
    question = "How many films are longer than 2 hours?"
    result = answer_question(question)

    print(f"Question: {result['question']}")
    print(f"SQL: {result['sql']}")
    print(f"Answer: {result['answer']}")
