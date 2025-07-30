# ✅ Flask route and LLM handler for chatbot analytics
from flask import Blueprint, render_template, request, jsonify, current_app
import sqlite3
import requests
import json
import re
from models import db

chat_bp = Blueprint("chat", __name__)

DB_PATH = "instance/prod_database.db"
OLLAMA_URL = "http://localhost:11434/api/generate"


# chatbot.py – Chatbot SQL interface for LLM-based analytics

import sqlite3
import requests
import re
from flask import Blueprint, render_template, request, current_app, session, redirect, url_for, flash
from models import db

chat_bp = Blueprint("chat", __name__)
OLLAMA_URL = "http://localhost:11434/api/generate"


def fetch_ollama_models():
    """Fetches available LLM models from the local Ollama server."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        data = response.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        print(f"❌ Error fetching Ollama models: {e}")
        return ["dolphin-mistral:latest"]


def generate_schema_prompt():
    """Generates a textual schema prompt based on current DB metadata."""
    important_tables = ["passport", "user", "activity", "signup", "redemption"]
    schema_sections = []

    for table in sorted(db.metadata.sorted_tables, key=lambda t: (t.name not in important_tables, t.name)):
        lines = [f'Table "{table.name}" (case-sensitive):']
        for column in table.columns:
            lines.append(f"- {column.name} ({column.type})")
        schema_sections.append("\n".join(lines))

    return "\n\n".join(schema_sections)


def get_prompt_template():
    """Returns the full prompt template including the schema and instructions."""
    schema_text = getattr(current_app, "SCHEMA_PROMPT", None)
    if not schema_text:
        schema_text = generate_schema_prompt()
        current_app.SCHEMA_PROMPT = schema_text

    return f"""
Tu es un assistant SQL. Voici les tables et colonnes disponibles dans la base de données (SQLite).

{schema_text}

⚠️ SQLite est sensible à la casse. Tu dois utiliser exactement les noms de tables et colonnes tels qu’ils sont affichés (ex: \"Passport\", \"User\").

Utilise DATE('now') pour aujourd’hui. Ne retourne que la requête SQL — sans explication.

Question: {{question}}
SQL:
"""


def call_ollama(question, model="dolphin-mistral:latest"):
    """Sends prompt to Ollama and returns the raw SQL string."""
    prompt_template = get_prompt_template()
    prompt = prompt_template.format(question=question)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        sql = data.get("response", "").strip()

        # 🧨 Remove markdown-style SQL code block formatting
        if sql.lower().startswith("```sql"):
            sql = sql[6:]
        if sql.endswith("```"):
            sql = sql[:-3]

        return sql.strip()

    except requests.exceptions.RequestException as e:
        return f"-- LLM error -- ({str(e)})"
    except ValueError:
        return "-- Invalid response from LLM --"


def sanitize_sql(raw_sql):
    """Cleans and validates incoming SQL for SQLite execution."""
    sql = raw_sql.strip()

    # 🔁 Convert MySQL-style functions to SQLite equivalents
    sql = re.sub(r'CURDATE\(\)', "DATE('now')", sql, flags=re.IGNORECASE)
    sql = re.sub(r'NOW\(\)', "'now'", sql, flags=re.IGNORECASE)
    sql = re.sub(r'EXTRACT\(YEAR_MONTH FROM ([^)]+)\)', r"strftime('%Y-%m', \1)", sql, flags=re.IGNORECASE)
    sql = re.sub(r'DATE_FORMAT\(([^,]+),\s*[\'\"]%Y-%m[\'\"]\)', r"strftime('%Y-%m', \1)", sql, flags=re.IGNORECASE)
    sql = re.sub(r'YEAR\(([^)]+)\)', r"strftime('%Y', \1)", sql, flags=re.IGNORECASE)
    sql = re.sub(r'MONTH\(([^)]+)\)', r"strftime('%m', \1)", sql, flags=re.IGNORECASE)
    sql = re.sub(r'GROUP BY MONTH\(([^)]+)\), YEAR\(\1\)', r"GROUP BY strftime('%Y-%m', \1)", sql, flags=re.IGNORECASE)
    sql = re.sub(r"DATE\('now'\)\s*-\s*INTERVAL\s*(\d+)\s*DAY", r"DATE('now', '-\1 days')", sql, flags=re.IGNORECASE)

    # 🔝 Remove short aliases like ep., p., r.
    sql = re.sub(r"\b[a-z]{1,3}\.", "", sql)

    # 💨 Block dangerous commands
    blocked = ["DELETE", "DROP", "INSERT", "UPDATE", "ALTER"]
    for keyword in blocked:
        if re.search(rf'\b{keyword}\b', sql, flags=re.IGNORECASE):
            return None, f"Blocked keyword in query: {keyword}"

    if not sql.lower().startswith("select"):
        return None, "Only SELECT statements are allowed."

    return sql, None


def run_sql_query(sql):
    """Runs SQL query against the configured SQLite DB and returns rows or error."""
    sql, error = sanitize_sql(sql)
    if error:
        return {"error": error}
    try:
        db_path = current_app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        if cursor.description is None:
            return {"error": "Query did not return rows."}
        cols = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return {"columns": cols, "rows": rows}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}"}


def detect_chart_type(question):
    """Infers chart type from user question keywords."""
    text = question.lower()
    if any(word in text for word in ["chart", "graph", "courbe", "graphe", "line"]):
        return "line"
    elif any(word in text for word in ["bar", "colonne", "histogramme"]):
        return "bar"
    return None


def parse_chart_data(result):
    """Parses DB result into {labels, values} for chart rendering."""
    if not result or not result.get("columns") or not result.get("rows"):
        return None
    cols = result["columns"]
    rows = result["rows"]
    if len(cols) < 2:
        return None
    labels = [str(row[0]) for row in rows]
    values = [row[1] for row in rows]
    return {"labels": labels, "values": values}







@chat_bp.route("/chat", methods=["GET", "POST"])
def chat():
    from flask import session, redirect, url_for, flash

    # 🔐 Admin-only access
    if "admin" not in session:
        flash("You must be logged in as admin to access the chatbot.", "error")
        return redirect(url_for("login"))

    models = fetch_ollama_models()
    selected_model = models[0] if models else "dolphin-mistral:latest"

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        selected_model = request.form.get("model", selected_model)
        chart_type = detect_chart_type(question)

        sql = call_ollama(question, model=selected_model)
        result = run_sql_query(sql)
        chart_data = parse_chart_data(result) if chart_type else None

        return render_template(
            "chat.html",
            question=question,
            sql=sql,
            result=result,
            selected_model=selected_model,
            chart_data=chart_data,
            chart_type=chart_type,
            models=models
        )

    return render_template("chat.html", models=models, selected_model=selected_model)
