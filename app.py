import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import streamlit as st
from pipeline import answer_question

st.set_page_config(page_title="NL2SQL RAG Agent", page_icon="🎬")

st.title("NL2SQL RAG Agent")
st.caption("Ask a question about the Sakila DVD-rental database in plain English.")

question = st.text_input("Your question", placeholder="How many films are longer than 2 hours?")

if st.button("Ask", type="primary") and question.strip():
    with st.spinner("Thinking..."):
        result = answer_question(question)

    st.subheader("Answer")
    st.write(result["answer"])

    if result["sql"]:
        with st.expander("Show SQL used"):
            st.code(result["sql"], language="sql")
