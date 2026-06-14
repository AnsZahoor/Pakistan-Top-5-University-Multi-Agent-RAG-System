"""Initial data seeding script for ChromaDB."""

import logging
from collections import Counter

from rag.scraper import scrape_all
from rag.vectorstore import add_documents, clear_collection, init_vectorstore

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    print("Starting scrape for all 5 universities...")
    docs = scrape_all()

    print("Initializing ChromaDB...")
    collection = init_vectorstore()
    clear_collection(collection)
    add_documents(collection, docs)

    counts = Counter(doc["university"] for doc in docs)
    print(f"\nSeeded {len(docs)} total chunks:")
    for uni in ["LUMS", "NUST", "PU", "FAST-NU", "AKU"]:
        print(f"  {uni}: {counts.get(uni, 0)} chunks")

    print("\nDone! Run `python app.py` to start the web server.")


if __name__ == "__main__":
    main()
