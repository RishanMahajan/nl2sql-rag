'''
This is essentially the file that lets your Python code talk to
the LLM (GPT, Claude, Gemini, etc.) through an API.

This file has three jobs:

Connect to Claude.
Send the prompt (built in prompt_builder).
Return the generated SQL.
'''

import os
import sys
import anthropic
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from prompt_builder import ANSWER_SYSTEM_PROMPT, build_answer_prompt

MODEL = "claude-haiku-4-5"

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client

# Construct a new synchronous Anthropic client instance. Now we've succesfully connected to claude

def clean_sql(text):
    """Strip markdown fences / stray whitespace the model sometimes adds despite instructions."""
    text = text.strip() # removes trailing and leading whitespaces from the returned query,if any
    if text.startswith("```"): # sometimes the returned query starts/ends with '''
        text = text.strip("`") # this removes the above
        if text.lower().startswith("sql"): # sometimes the query is like 'sql select* from...' and so on
            text = text[3:] # removes the 'sql' part
    return text.strip().rstrip(";").strip() + ";" # removes spaces,every semicolon. then adds one semicolon in the end

# this whole function just cleans the sql query returned by the llm.

def generate_sql(system_prompt, user_prompt):
    """Call Claude with the built prompt and return cleaned SQL text."""
    client = get_client() 
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt, # this is that "You are an sql expert" message.Sent to claude before sending the user prompt(context+user question+instructions)
        messages=[{"role": "user", "content": user_prompt}],
    ) # claude returns a query but in the form of an object. it doesnt simply return a string
    raw = next(block.text for block in response.content if block.type == "text") # this extracts the query string
    return clean_sql(raw) # this cleans the extracted query


def generate_answer(question, rows):
    """Stage 8: turn raw query result rows into a plain-English answer."""
    client = get_client()
    prompt = build_answer_prompt(question, rows)
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=ANSWER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = next(block.text for block in response.content if block.type == "text")
    return raw.strip()


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from retrieval.vector_store import query_schema
    from generation.prompt_builder import SYSTEM_PROMPT, build_prompt

    question = "How many films are longer than 2 hours?"
    chunks = query_schema(question)
    prompt = build_prompt(question, chunks)

    sql = generate_sql(SYSTEM_PROMPT, prompt)
    print(f"Question: {question}")
    print(f"Generated SQL: {sql}")
