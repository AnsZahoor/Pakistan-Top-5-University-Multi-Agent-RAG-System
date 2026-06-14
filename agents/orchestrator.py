"""Orchestrator agent — routes student queries to the right university agent."""

import json
import logging
import os
import re

from anthropic import Anthropic
from dotenv import load_dotenv

from agents.prompts import ALL_UNIVERSITIES, ORCHESTRATOR_SYSTEM_PROMPT

load_dotenv()
logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
VALID_QUERY_TYPES = {"admissions", "fees", "programs", "contact", "general"}


class Orchestrator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise ValueError("ANTHROPIC_API_KEY is not set in .env")
        self.client = Anthropic(api_key=api_key)

    def classify(self, question: str) -> dict:
        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=100,
                system=ORCHESTRATOR_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": question}],
            )
            raw = response.content[0].text.strip()
            return self._parse_response(raw, question)
        except Exception as exc:
            logger.error("Orchestrator classification failed: %s", exc)
            return self._fallback_classify(question)

    def _parse_response(self, raw: str, question: str) -> dict:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return self._fallback_classify(question)

        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return self._fallback_classify(question)

        university = data.get("university", "all")
        query_type = data.get("query_type", "general")

        if university not in ALL_UNIVERSITIES and university != "all":
            university = "all"
        if query_type not in VALID_QUERY_TYPES:
            query_type = "general"

        return {"university": university, "query_type": query_type}

    def _fallback_classify(self, question: str) -> dict:
        lowered = question.lower()
        matched = []

        aliases = {
            "LUMS": ["lums", "lahore university of management"],
            "NUST": ["nust", "national university of sciences"],
            "PU": ["punjab university", "university of the punjab", " pu "],
            "FAST-NU": ["fast", "fast-nu", "nu.edu.pk"],
            "AKU": ["aku", "aga khan"],
        }

        for uni, terms in aliases.items():
            if any(term in lowered for term in terms):
                matched.append(uni)

        university = matched[0] if len(matched) == 1 else "all"

        query_type = "general"
        if any(word in lowered for word in ["admission", "apply", "entry test", "deadline"]):
            query_type = "admissions"
        elif any(word in lowered for word in ["fee", "tuition", "cost", "scholarship"]):
            query_type = "fees"
        elif any(word in lowered for word in ["program", "department", "degree", "major", "course"]):
            query_type = "programs"
        elif any(word in lowered for word in ["contact", "phone", "email", "address", "location"]):
            query_type = "contact"

        return {"university": university, "query_type": query_type}
