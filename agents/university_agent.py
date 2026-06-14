"""University-specific agent that answers using retrieved RAG context."""

import logging
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from agents.prompts import UNIVERSITY_PROMPTS
from rag.scraper import get_university_domain

load_dotenv()
logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"


class UniversityAgent:
    def __init__(self, university_name: str):
        if university_name not in UNIVERSITY_PROMPTS:
            raise ValueError(f"Unknown university: {university_name}")
        self.university_name = university_name
        self.system_prompt = UNIVERSITY_PROMPTS[university_name]
        self.domain = get_university_domain(university_name)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise ValueError("ANTHROPIC_API_KEY is not set in .env")
        self.client = Anthropic(api_key=api_key)

    def answer(self, question: str, retrieved_context: str) -> str:
        if not retrieved_context.strip():
            return (
                f"I don't have that information right now — please visit "
                f"{self.domain} or contact admissions.\n"
                f"Source: {self.domain}"
            )

        user_message = (
            f"Student question: {question}\n\n"
            f"Retrieved context from {self.university_name} website:\n"
            f"{retrieved_context}\n\n"
            "Answer the question using only the context above. "
            "Include a Source line at the end citing the most relevant URL from the context."
        )

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=800,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text.strip()
        except Exception as exc:
            logger.error("%s agent failed: %s", self.university_name, exc)
            return (
                "Sorry, I'm having trouble reaching the AI service right now. "
                f"Please try again later or visit {self.domain} directly.\n"
                f"Source: {self.domain}"
            )
