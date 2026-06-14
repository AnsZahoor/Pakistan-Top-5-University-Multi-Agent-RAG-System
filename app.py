"""Flask application entry point for the Pakistan University Multi-Agent RAG system."""

import logging
import os
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from agents.orchestrator import Orchestrator
from agents.prompts import ALL_UNIVERSITIES
from agents.university_agent import UniversityAgent
from rag.scraper import scrape_all
from rag.vectorstore import add_documents, get_document_count, init_vectorstore, query
from scheduler.refresh import start_scheduler

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
vectorstore = None
orchestrator = None


def ensure_vectorstore_populated():
    global vectorstore
    vectorstore = init_vectorstore()
    count = get_document_count(vectorstore)

    if count == 0:
        logger.info("Vector store empty — scraping and seeding data...")
        docs = scrape_all()
        add_documents(vectorstore, docs)
        logger.info("Seeded %d document chunks", len(docs))
    else:
        logger.info("Vector store loaded with %d documents", count)


def handle_query(user_question: str) -> str:
    routing = orchestrator.classify(user_question)
    university = routing.get("university", "all")

    if university == "all":
        universities_to_query = ALL_UNIVERSITIES
    else:
        universities_to_query = [university]

    responses = []
    for i, uni in enumerate(universities_to_query):
        if i > 0:
            time.sleep(5)

        context_chunks = query(vectorstore, user_question, university=uni, top_k=3)
        context_text = "\n\n".join([c["text"] for c in context_chunks])

        agent = UniversityAgent(uni)
        answer = agent.answer(user_question, context_text)
        responses.append(f"**{uni}:**\n{answer}")

    return "\n\n---\n\n".join(responses)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"response": "Please enter a question about one of the universities."}), 400

    try:
        response_text = handle_query(message)
        return jsonify({"response": response_text})
    except Exception as exc:
        logger.error("Chat error: %s", exc)
        return jsonify(
            {
                "response": (
                    "Sorry, something went wrong while processing your question. "
                    "Please try again in a moment."
                )
            }
        ), 500


if __name__ == "__main__":
    ensure_vectorstore_populated()
    try:
        orchestrator = Orchestrator()
        print("[Startup] Orchestrator initialized with Gemini.")
    except Exception as e:
        print(f"[Startup ERROR] Failed to initialize Orchestrator: {e}")
        raise
    # Avoid starting the scheduler twice when Flask debug reloader is active.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler()
    app.run(debug=True, host="127.0.0.1", port=5000)
