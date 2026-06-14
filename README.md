# Pakistan Top-5 University Multi-Agent RAG System

A multi-agent Retrieval-Augmented Generation (RAG) system that helps Pakistani students get accurate, up-to-date answers about **LUMS**, **NUST**, **PU**, **FAST-NU**, and **AKU** — powered by Claude and scraped data from each university's official website.

## Architecture

```
Student (Browser)
     ↓
Flask Web Interface
     ↓
Orchestrator Agent (routes query to university)
     ↓
University Agent (one per university)
     ↓
ChromaDB RAG Retrieval
     ↓
Claude API (grounded answer)
```

## Tech Stack

- **Backend:** Python, Flask
- **LLM:** Anthropic Claude (`claude-sonnet-4-6`)
- **Vector Store:** ChromaDB + `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Scraping:** BeautifulSoup4 + Requests
- **Scheduler:** APScheduler (24-hour auto-refresh)

## Setup

### 1. Prerequisites

- Python 3.11+
- Anthropic API key

### 2. Install dependencies

```bash
cd pakistan_uni_agent
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment

Copy the example env file and add your API key:

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `.env`:

```
ANTHROPIC_API_KEY=your_actual_key_here
```

### 4. Seed the vector database (recommended first run)

```bash
python seed.py
```

This scrapes all 5 university websites and populates ChromaDB. Expect a few minutes due to rate limiting.

### 5. Start the Flask server

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

> **Note:** If you skip `seed.py`, the app will auto-scrape on first startup when ChromaDB is empty.

## Usage Examples


| Question                                    | Routed To                                        |
| ------------------------------------------- | ------------------------------------------------ |
| "What are LUMS admission requirements?"     | LUMS                                             |
| "Compare NUST and FAST CS programs"         | NUST + FAST-NU (+ others if classified as `all`) |
| "What is the fee at AKU medical?"           | AKU                                              |
| "Which university is best for engineering?" | All 5 universities                               |


## Project Structure

```
pakistan_uni_agent/
├── app.py                    # Flask entry point
├── seed.py                   # One-time data seeding
├── requirements.txt
├── agents/
│   ├── orchestrator.py       # Query routing
│   ├── university_agent.py   # Per-university Claude agent
│   └── prompts.py            # System prompts
├── rag/
│   ├── scraper.py            # Website scraper
│   ├── vectorstore.py        # ChromaDB operations
│   └── embeddings.py         # Sentence-transformers wrapper
├── scheduler/
│   └── refresh.py            # 24-hour auto-refresh
├── templates/
│   └── index.html            # Chat UI
├── static/
│   └── style.css
└── data/
    └── chroma_db/            # Persisted vectors (auto-created)
```

## Key Behaviors

- Agents answer **only** from scraped context — no hallucinated fees or dates
- Responses include a **Source:** URL footer
- Scraping is rate-limited (1 second between requests)
- Data refreshes automatically every **24 hours** via APScheduler
- ChromaDB queries are filtered by university metadata

## Troubleshooting


| Issue                          | Fix                                                                        |
| ------------------------------ | -------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY is not set` | Add your key to `.env`                                                     |
| Empty or weak answers          | Run `python seed.py` to refresh scraped data                               |
| Scraper warnings               | Some university pages may be unavailable; the system skips them gracefully |
| Slow first startup             | Initial scrape + embedding download takes time on first run                |


## License

Built for Pakistani students — accurate, fast, helpful.