""" In the last file we made chunks out of separate tables. now we will
now we'll convert these chunks to vectors (embeddings). similar sentences
have almost identical vectors. the dataset contains 'films' and 'length'
but what if someone asked "List the movies(not films) with duration(not length)
more than 2 hours.if chunks werent embedded, model wont know that film and
movies are same. same for length and duration
"""


import os
import chromadb
from sentence_transformers import SentenceTransformer

PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chroma_db")
# creates chroma_db under nl2sql-rag-agent. this stores our vectors
COLLECTION_NAME = "schema_chunks"
# collections are to chroma_db what tables are to mysql

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model
# just loaded the model into the variable _model. This model converts 
# both(user query, dataset chunks) into 384 dimensional vector.

def get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    return client.get_or_create_collection(COLLECTION_NAME)
# this is just like conn=get_connection(). instead of opening mysql,
# you're opening chroma db. and it returns schema_chunks if it exists.
# it it doesnt, it creates it and returns it


def build_index(chunks):
    """Embed each schema chunk and store it in Chroma. Wipes and rebuilds the collection."""
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    client.delete_collection(COLLECTION_NAME) if COLLECTION_NAME in [c.name for c in client.list_collections()] else None
    collection = client.get_or_create_collection(COLLECTION_NAME)
    #opens chroma db. if schema_chunks already exists, it deletes it 
    # and creates a new one.

    model = get_embedding_model()
    texts = [chunk["text"] for chunk in chunks]
    ids = [chunk["table_name"] for chunk in chunks]
    embeddings = model.encode(texts).tolist()
    # each chunk has 2 parts, table name and text. this converts the
    # text into vectors

    collection.add(ids=ids, embeddings=embeddings, documents=texts)
    # we add (table_name,vector,text) to schema_chunks for each table
    return collection


def query_schema(question, top_k=3):
    """Embed the question and return the top_k closest schema chunks."""
    model = get_embedding_model()
    question_embedding = model.encode([question]).tolist()
    # Converts the user question into a vector

    collection = get_collection() # open chroma db
    results = collection.query(query_embeddings=question_embedding, n_results=top_k)

    """
     we didnt do collection.add as we dont want to add the user question
     to the schema_chunks we only want to compare the question with what
     is present already in schema_chunks.That is exactly what the query 
     function does. it finds the nearest neighbours.
     """

    return results["documents"][0]


if __name__ == "__main__":
    from embed_schema import fetch_table_schemas, build_schema_chunks

    tables = fetch_table_schemas()
    chunks = build_schema_chunks(tables)
    build_index(chunks)
    print(f"Indexed {len(chunks)} tables into Chroma at {PERSIST_DIR}")

    test_question = "How many films are longer than 2 hours?"
    top_matches = query_schema(test_question)
    print(f"\nTop matches for: '{test_question}'")
    for match in top_matches:
        print(f" - {match}")

'''
This file implements the "R" (Retrieval) in RAG:

1.Convert each schema chunk into an embedding.
2.Store those embeddings in ChromaDB.
3.When a user asks a question, convert the question into an embedding.
4.Use vector similarity search to retrieve the most relevant schema chunks.
5.Pass those retrieved chunks to the LLM so it has the right database context before generating SQL.
'''