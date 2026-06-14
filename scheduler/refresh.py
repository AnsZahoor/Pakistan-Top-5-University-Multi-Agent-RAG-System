"""APScheduler job to refresh scraped university data every 24 hours."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from rag.scraper import scrape_all
from rag.vectorstore import add_documents, clear_collection, init_vectorstore

logger = logging.getLogger(__name__)


def refresh_data():
    logger.info("[Scheduler] Starting data refresh...")
    docs = scrape_all()
    vs = init_vectorstore()
    clear_collection(vs)
    added = add_documents(vs, docs)
    logger.info("[Scheduler] Refreshed %d chunks from university websites", added)
    print(f"[Scheduler] Refreshed {added} chunks from university websites")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_data, "interval", hours=24, id="refresh_university_data")
    scheduler.start()
    logger.info("[Scheduler] Started — refresh every 24 hours")
    return scheduler
