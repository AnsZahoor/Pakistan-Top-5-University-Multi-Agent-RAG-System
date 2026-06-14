import json
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class Orchestrator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def classify(self, question: str) -> dict:
        prompt = f"""You are a router for Pakistani university queries.
Given this student question, identify:
1. Which university it refers to: LUMS, NUST, PU, FAST-NU, AKU, or "all"
2. Query type: admissions, fees, programs, contact, or general

Respond ONLY with valid JSON. No markdown, no backticks, no explanation.
Example: {{"university": "LUMS", "query_type": "admissions"}}
If unsure about university, use "all".

Student question: {question}"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"[Orchestrator] Error: {e}")
            return {"university": "all", "query_type": "general"}
