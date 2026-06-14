import os
import time

import google.generativeai as genai
from dotenv import load_dotenv

from agents.prompts import PROMPTS

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def trim_context(context: str, max_chars: int = 2000) -> str:
    """Trim context to avoid hitting token limits on free tier."""
    return context[:max_chars] + "..." if len(context) > max_chars else context


class UniversityAgent:
    def __init__(self, university_name: str):
        self.university_name = university_name
        self.system_prompt = PROMPTS.get(university_name, PROMPTS["DEFAULT"])

    def answer(self, question: str, retrieved_context: str, max_retries: int = 3) -> str:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-8b",
            system_instruction=self.system_prompt,
        )

        context_text = trim_context(retrieved_context, max_chars=2000)

        if context_text.strip():
            prompt = f"""Use the following context to answer the student's question.
Cite the source URL at the end if available in the context.

Context:
{context_text}

Student Question: {question}"""
        else:
            prompt = f"""A student asked: {question}
No context was retrieved. Politely tell them you don't have that specific information and direct them to the official website."""

        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    wait = (attempt + 1) * 20
                    print(
                        f"[{self.university_name}] Rate limited. "
                        f"Waiting {wait}s before retry {attempt + 1}/{max_retries}..."
                    )
                    time.sleep(wait)
                else:
                    return f"Sorry, I encountered an error. Please try again. (Error: {error_str})"

        return "I'm currently experiencing high demand. Please try again in a minute."
