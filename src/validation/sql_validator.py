"""
up until now, we've generated the sql query, but we dont have any mechanism to check whether the generated
query
"""

import re

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "REPLACE", "GRANT", "REVOKE", "EXEC", "MERGE", "ATTACH",
]

# It contains SQL commands that should never be executed.because your chatbot is supposed to read data, not 
# modify it. because below is a line that says 'cursor.execute(f"EXPLAIN {sql}")'. if a delete statement is
# executed, you might lose data permanently


def is_select_only(sql):
    """Reject anything that isn't a single, plain SELECT statement."""
    stripped = sql.strip().rstrip(";").strip() #removes whitespaces,semicolons from right side, then again leftover spaces are removed

    if not stripped.upper().startswith("SELECT"):
        return False, "Query must start with SELECT." # rejects any statement not starting with select

    if ";" in stripped: 
        return False, "Only a single statement is allowed." # we removed all sc. if it still exists it means there were multiple statements

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", stripped, re.IGNORECASE):
            return False, f"Forbidden keyword found: {keyword}."
            # if forbidden keyword is found, returns tuple (false,Forbidden keyword found: {keyword})
    return True, None


def extract_table_names(sql):
    """Pull table names referenced after FROM / JOIN."""
    matches = re.findall(r"(?:FROM|JOIN)\s+`?(\w+)`?", sql, re.IGNORECASE)
    return {m.lower() for m in matches}


def validate_tables(sql, known_tables):
    """Check every referenced table actually exists in the schema."""
    known_lower = {t.lower() for t in known_tables}
    used_tables = extract_table_names(sql)
    unknown = used_tables - known_lower

    if unknown:
        return False, f"Unknown table(s): {', '.join(sorted(unknown))}."

    return True, None

# these 2 functions just checks Do all referenced tables exist?


def validate_syntax(sql):
    """Ask MySQL to plan (not run) the query — catches syntax/schema errors without touching data."""
    import mysql.connector
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from execution.db_connector import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"EXPLAIN {sql}")
        cursor.fetchall()
        return True, None
    except mysql.connector.Error as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()


def validate(sql, known_tables):
    """Run all checks in order; return (is_valid, error_message)."""
    ok, error = is_select_only(sql)
    if not ok:
        return False, error

    ok, error = validate_tables(sql, known_tables)
    if not ok:
        return False, error

    ok, error = validate_syntax(sql)
    if not ok:
        return False, error

    return True, None


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from retrieval.embed_schema import fetch_table_schemas

    known_tables = fetch_table_schemas().keys()

    test_queries = [
        "SELECT COUNT(*) FROM film WHERE length > 120;",
        "SELECT * FROM made_up_table;",
        "DROP TABLE film;",
        "SELECT * FROM film WHERE length >> 120;",
    ]

    for q in test_queries:
        is_valid, error = validate(q, known_tables)
        status = "VALID" if is_valid else f"INVALID ({error})"
        print(f"{q!r} -> {status}")
