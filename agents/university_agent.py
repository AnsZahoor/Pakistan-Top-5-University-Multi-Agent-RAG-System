import os

import google.generativeai as genai
from dotenv import load_dotenv

from agents.prompts import PROMPTS

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class UniversityAgent:
    def __init__(self, university_name: str):
        self.university_name = university_name
        self.system_prompt = PROMPTS.get(university_name, PROMPTS["DEFAULT"])

    def answer(self, question: str, retrieved_context: str) -> str:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=self.system_prompt,
        )

        if retrieved_context.strip():
            prompt = f"""Use the following context to answer the student's question.
Always cite the source URL at the end if available in the context.

Context:
{retrieved_context}

Student Question: {question}"""
        else:
            prompt = f"""A student asked: {question}
No context was retrieved from the database. Politely tell them you don't have that specific information and direct them to the official website."""

        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return (
                "Sorry, I encountered an error while generating a response. "
                f"Please try again. (Error: {str(e)})"
            )
