# nl2sql-rag-agent

Ask a database a question in plain English, get a plain English answer back — with the SQL it ran shown alongside for transparency.

```
Q: How many films are longer than 2 hours?
SQL: SELECT COUNT(*) FROM film WHERE length > 120;
A: There are 457 films that are longer than 2 hours.
```

## How it works

The core idea is Retrieval-Augmented Generation (RAG) applied to SQL generation: instead of dumping the entire database schema into every prompt, only the tables relevant to the question are retrieved and shown to the LLM.

1. **Index the schema (once).** Every table's structure is pulled from `INFORMATION_SCHEMA`, turned into a text description, embedded, and stored in a local Chroma vector database.
2. **Embed the question.** The user's question is embedded with the same model used for the schema.
3. **Retrieve relevant tables.** A vector similarity search returns only the 2–3 tables most relevant to the question, instead of the whole schema.
4. **Build the prompt.** The retrieved schema + the question + instructions are assembled into a prompt.
5. **Generate SQL.** An LLM call turns the prompt into a MySQL query.
6. **Validate.** The query is checked before it ever touches real data: `SELECT`-only, no destructive keywords, referenced tables actually exist, and `EXPLAIN` confirms it's syntactically valid against the live schema.
7. **Retry on failure.** If validation fails, the specific error is fed back to the LLM so it can fix its own mistake — up to a few attempts.
8. **Execute.** The validated query runs against the real MySQL database.
9. **Summarize.** The raw rows are turned into a short, plain-English answer, grounded strictly in the returned data (no hallucinated results).

## Project structure

```
src/
  retrieval/
    embed_schema.py     # pulls schema from MySQL, turns tables into text chunks
    vector_store.py      # embeds chunks with Chroma, retrieves relevant tables per question
  generation/
    prompt_builder.py    # builds the SQL-generation and answer-summary prompts
    llm_client.py         # calls the Claude API, cleans SQL output, generates answers
  validation/
    sql_validator.py     # SELECT-only check, table existence check, EXPLAIN-based syntax check
  execution/
    db_connector.py       # MySQL connection + query execution
    retry_handler.py     # generate -> validate -> retry-on-failure loop
  pipeline.py              # wires everything into one function: answer_question(question)
data/
  sakila-schema.sql       # sample database schema (MySQL's Sakila DVD-rental dataset)
  sakila-data.sql         # sample data
```

## Setup

**1. Create a virtual environment and install dependencies**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**2. Set up MySQL with the Sakila sample database**

Load `data/sakila-schema.sql` followed by `data/sakila-data.sql` into a local MySQL instance.

**3. Create a `.env` file** in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
MYSQL_HOST=localhost
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=sakila
```

**4. Build the schema index** (one-time setup — rerun whenever the schema changes)

```bash
python src/retrieval/vector_store.py
```

## Usage

```python
from pipeline import answer_question

result = answer_question("How many films are longer than 2 hours?")
print(result["sql"])
print(result["answer"])
```

Or run the pipeline directly for a quick check:

```bash
python src/pipeline.py
```

## Tech stack

| Piece | Tool |
|---|---|
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| Vector store | ChromaDB (local, persistent) |
| LLM | Claude (`claude-haiku-4-5`) via the Anthropic API |
| Database | MySQL (Sakila sample dataset) |
