import streamlit as st
# from dotenv import load_dotenv
from openai import OpenAI
import os
import re


#oad_dotenv()

def get_schema_with_values(df):
    schema_lines = []

    for col in df.columns:
        dtype = str(df[col].dtype)

        line = f"- {col} ({dtype})"

        # If column is categorical-like, show example values
        if df[col].dtype == "object" or df[col].nunique() < 10:
            unique_vals = df[col].dropna().unique()[:5]
            line += f" possible values: {list(unique_vals)}"

        schema_lines.append(line)

    return "\n".join(schema_lines)

def generate_sql(question, schema):
    prompt = f"""
                You are a SQLite expert.

                Table name: data

                Columns:
                {schema}

                Rules:
                - Only generate SELECT queries.
                - Do NOT use INSERT, UPDATE, DELETE, DROP.
                - Return ONLY valid SQLite SQL.
                - Do not explain anything.
                - String values MUST be wrapped in single quotes.
                - Use exact values shown in possible values.
                - SQLite is case sensitive for string comparisons.
                - Always use correct casing.

                User Question:
                {question}
                """
    
    # client = OpenAI(
    #     api_key=os.getenv("GROQ_API_KEY"),
    #     base_url="https://api.groq.com/openai/v1"
    # )

    client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()


def clean_sql_output(sql):
    # Remove markdown code fences like ```sql ... ```
    sql = re.sub(r"```.*?\n", "", sql)  # remove opening ```sql
    sql = sql.replace("```", "")        # remove closing ```
    return sql.strip()


def validate_sql(sql):
    sql_lower = sql.lower().strip()

    if not sql_lower.startswith("select"):
        raise Exception("Only SELECT queries are allowed.")

    forbidden = ["insert", "update", "delete", "drop", "pragma"]
    for word in forbidden:
        if word in sql_lower:
            raise Exception("Unsafe SQL detected.")

    return sql