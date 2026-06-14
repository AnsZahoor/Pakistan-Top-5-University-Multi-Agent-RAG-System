"""Web scraper for Pakistan top-5 university websites."""

import logging
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

UNIVERSITIES = {
    "LUMS": {
        "name": "Lahore University of Management Sciences",
        "base_url": "https://lums.edu.pk",
        "pages": {
            "homepage": "/",
            "admissions": "/admissions-and-aid",
            "programs": "/programs-degrees",
            "fees": "/student-financial-services/tuition-and-fees",
            "contact": "/contact-us",
        },
    },
    "NUST": {
        "name": "National University of Sciences & Technology",
        "base_url": "https://nust.edu.pk",
        "pages": {
            "homepage": "/",
            "admissions": "/admissions",
            "programs": "/programs",
            "fees": "/fee-structure",
            "contact": "/contact",
        },
    },
    "PU": {
        "name": "University of the Punjab",
        "base_url": "https://pu.edu.pk",
        "pages": {
            "homepage": "/",
            "admissions": "/page/admissions",
            "programs": "/page/departments",
            "fees": "/page/fee-structure",
            "contact": "/page/contact-us",
        },
    },
    "FAST-NU": {
        "name": "FAST National University",
        "base_url": "https://nu.edu.pk",
        "pages": {
            "homepage": "/",
            "admissions": "/Admissions",
            "programs": "/Programs",
            "fees": "/FeeStructure",
            "contact": "/ContactUs",
        },
    },
    "AKU": {
        "name": "Aga Khan University",
        "base_url": "https://aku.edu",
        "pages": {
            "homepage": "/",
            "admissions": "/admissions",
            "programs": "/academics",
            "fees": "/admissions/tuition-fees",
            "contact": "/about/contact-us",
        },
    },
}


def _estimate_tokens(text: str) -> int:
    return len(text.split())


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start = max(end - overlap, start + 1)

    return chunks


def _clean_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fetch_page(url: str) -> str | None:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        content_type = response.headers.get("Content-Type", "")
        if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
            logger.warning("Skipping PDF: %s", url)
            return None

        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return None


def _scrape_page(url: str) -> str:
    html = _fetch_page(url)
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    return _clean_text(soup)


def scrape_university(university_key: str) -> list[dict]:
    config = UNIVERSITIES[university_key]
    base_url = config["base_url"]
    documents = []

    for page_type, path in config["pages"].items():
        url = urljoin(base_url, path)
        logger.info("Scraping %s (%s): %s", university_key, page_type, url)

        text = _scrape_page(url)
        time.sleep(1)

        if not text:
            continue

        for chunk in _chunk_text(text):
            documents.append(
                {
                    "university": university_key,
                    "url": url,
                    "page_type": page_type,
                    "text": chunk,
                }
            )

    return documents


def scrape_all() -> list[dict]:
    all_docs = []
    for university_key in UNIVERSITIES:
        docs = scrape_university(university_key)
        all_docs.extend(docs)
        logger.info("Scraped %d chunks for %s", len(docs), university_key)
    return all_docs


def get_university_domain(university_key: str) -> str:
    base_url = UNIVERSITIES[university_key]["base_url"]
    parsed = urlparse(base_url)
    return parsed.netloc or base_url
