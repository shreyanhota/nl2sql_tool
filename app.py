import streamlit as st
import os
import pandas as pd
import sqlite3
from llm import get_schema_with_values,generate_sql,clean_sql_output

# import seaborn as sns
# df = sns.load_dataset("titanic")

current_dir = os.getcwd()
data_dir = os.path.join(current_dir, "data")
file_path = os.path.join(data_dir, "titanic.csv")

st.set_page_config(page_title="NL → SQL Tool", layout="wide")
st.title("Natural Language → SQL Query Tool")

# Upload or default
uploaded_file = st.file_uploader("Upload CSV (optional)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_csv(file_path)

schema_context = get_schema_with_values(df)

# SQLite in-memory DB
conn = sqlite3.connect(":memory:")
df.to_sql("data", conn, index=False, if_exists="replace")

st.subheader("Dataset Preview")
st.dataframe(df.head())

question = st.text_input("Enter your question")

def is_safe_query(query):
    sql_lower = query.lower().strip()
    forbidden = ["insert", "update", "delete", "drop", "pragma"]
    return not any(word in sql_lower for word in forbidden)

def execute_sql(sql):
    cursor = conn.cursor()
    cursor.execute(sql)
    return cursor.fetchall()


if st.button("Run Query"):

    if not question:
        st.warning("Please enter a question.")
    else:
        try:
            sql_query = generate_sql(question, schema_context)
            cleaned_query = clean_sql_output(sql_query)

            st.subheader("Generated SQL")
            st.code(sql_query, language="sql")

            if not is_safe_query(sql_query):
                st.error("Unsafe query detected.")
            else:
                result = execute_sql(cleaned_query)

                st.subheader("Result")
                st.dataframe(result)

        except Exception as e:
            st.error(f"Error: {e}")