# ⚡ Tech Pulse

A personal tech intelligence dashboard that tracks trending topics from Hacker News and helps you build a searchable, AI-summarized knowledge base.

**[🔗 Live Demo](tech-pulse-hb7av7rossiqklrxbqbeun.streamlit.app)** ← *replace with your actual URL after deployment*

## Features

### 📈 Trend Tracker
- Fetches top stories from Hacker News in real-time
- Uses Claude AI to auto-categorize articles (AI/ML, Web Dev, Security, etc.)
- Generates one-sentence summaries for each article
- Visualizes category distribution with bar charts
- Tracks topic momentum over time with trend line charts
- Search and filter by category or keyword

### 🔖 Personal Knowledge Base
- Save any article by pasting its URL
- AI automatically generates:
  - 2-3 sentence summary
  - Relevant tags
  - Difficulty rating (beginner / intermediate / advanced)
- Add and edit your own notes on saved articles
- Search and filter by tags or keywords

## Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python** | Core language |
| **Streamlit** | Web framework (frontend + backend) |
| **SQLite** | Database for persistent storage |
| **Claude API** (Haiku) | AI categorization and summarization |
| **Hacker News API** | Source of trending tech content |
| **BeautifulSoup** | Web scraping for bookmark content extraction |

## Architecture

```
[Data Sources]          [Processing]           [Storage]        [Frontend]
 Hacker News API  ──→  hn_fetcher.py    ──→                 ┌─ app.py (Home)
 User URLs        ──→  web_scraper.py   ──→   SQLite DB  ──→├─ 1_Trends.py
                        llm_service.py   ──→                 └─ 2_Bookmarks.py
                        (Claude API)
```

## Project Structure

```
tech-pulse/
├── app.py                  # Home page with stats overview
├── pages/
│   ├── 1_Trends.py         # Trend tracker dashboard
│   └── 2_Bookmarks.py      # Personal knowledge base
├── services/
│   ├── hn_fetcher.py       # Hacker News API integration
│   ├── llm_service.py      # Claude API for AI analysis
│   ├── web_scraper.py      # Article content extraction
│   └── db.py               # SQLite database operations
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.10+
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/tech-pulse.git
cd tech-pulse

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Edit .env and add your Anthropic API key

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### Usage
1. **Track trends**: Go to the Trends page and click "Fetch New Stories" to pull and analyze the latest from Hacker News.
2. **Save bookmarks**: Go to the Bookmarks page, paste any article URL, and get an AI-generated summary and tags.
3. **Build over time**: Fetch stories regularly to build up trend data and watch topic momentum change.

## Cost

This project uses Claude Haiku, the most affordable model. Typical costs:
- Categorizing 30 HN articles: ~$0.01
- Analyzing a bookmark: ~$0.005
- Total for building and testing: under $5

## License

MIT
