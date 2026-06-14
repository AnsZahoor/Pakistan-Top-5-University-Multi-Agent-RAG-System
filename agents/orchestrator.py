import json
import os
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class Orchestrator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash-8b")

    def classify(self, question: str) -> dict:
        prompt = f"""You are a router for Pakistani university queries.
Identify:
1. University: LUMS, NUST, PU, FAST-NU, AKU, or "all"
2. Query type: admissions, fees, programs, contact, or general

IMPORTANT: If the question is about ONE specific university, return ONLY that university — do NOT use "all".
Respond ONLY with valid JSON, no markdown.
Example: {{"university": "LUMS", "query_type": "admissions"}}

Student question: {question}"""

        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)
                text = response.text.strip().replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            except Exception as e:
                if "429" in str(e):
                    time.sleep(10)
                else:
                    print(f"[Orchestrator] Error: {e}")
                    return {"university": "all", "query_type": "general"}

        return {"university": "all", "query_type": "general"}
