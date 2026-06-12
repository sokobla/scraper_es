# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**scrapper_spain** est un scraper web asynchrone conçu pour collecter des données depuis le site paginasamarillas.es (pages jaunes espagnoles). Le projet utilise Flask comme framework backend, Playwright pour le scraping, et PostgreSQL comme base de données.

### Tech Stack
- **Backend**: Flask 3.1.3, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.50
- **Scraping**: Playwright 1.60.0 avec Stealth Mode
- **Database**: PostgreSQL (via psycopg2-binary)
- **Configuration**: YAML (PyYAML 6.0.3)
- **Async Runtime**: asyncio (built-in Python)
- **Containerization**: Docker & docker-compose
- **Python**: 3.11

## Project Structure (Planned)

```
scrapper_spain/
├── run_scrapper.py           # Entry point - orchestrates scraping by categories
├── config.yml               # Configuration file with database & categories
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Local dev environment orchestration
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy ORM models (Business, Contact, etc.)
│   └── session.py          # DB session initialization (init_db)
├── scraper/
│   ├── __init__.py
│   ├── scraper_runner.py   # Main scraping orchestrator (ScraperRunner)
│   ├── browser_manager.py  # Playwright browser lifecycle
│   └── parsers.py          # HTML parsing & data extraction
├── utils/
│   ├── __init__.py
│   └── logger.py           # Logging setup (build_logger)
└── tests/                  # Unit & integration tests (not yet created)
```

## Commands

### Setup & Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate environment (Windows)
.venv\Scripts\activate
# Or (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for scraping)
playwright install
```

### Running the Application

#### Local Development (Direct Python)
```bash
# Run the main scraper
python run_scrapper.py

# Expected behavior:
# 1. Load categories from config.yml
# 2. Initialize database
# 3. Iterate over categories and scrape paginasamarillas.es
# 4. Save results to PostgreSQL
```

#### Docker Environment
```bash
# Start services (PostgreSQL + App)
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f scraper

# Run single service
docker-compose up db  # Just PostgreSQL
```

### Database

#### Local PostgreSQL (Manual Setup)
```bash
# Connection string from config.yml
postgresql://scrapper_user:scrapper_password@localhost:5432/scrapper_db

# Using psql directly
psql postgresql://scrapper_user:scrapper_password@localhost:5432/scrapper_db
```

#### Migrations
**Status**: Not yet implemented. When adding:
- Use Flask-Migrate (Alembic wrapper)
- Store migrations in `database/migrations/`
- Run: `flask db upgrade` before deploying

## Architecture Notes

### Entry Point Flow (`run_scrapper.py`)
1. **Config Loading**: Reads `config.yml` to get categories (Gym, dépôt, cochera, almacenar)
2. **Database Init**: Calls `database.session.init_db()` to set up tables
3. **Scraper Orchestration**: Creates `ScraperRunner(headless=True, max_pages=3)` instance
4. **Async Loop**: For each category, runs `await runner.run(category)` to scrape and store data
5. **Error Handling**: Logs success/failure per category; continues on errors

### Key Modules to Implement

#### `database/models.py`
Define ORM models for:
- **Business**: name, address, phone, email, website, category_name
- **Contact**: business_id, contact_method, value
- **Category**: name, description, image_url (matches config.yml)
- Add timestamp fields (created_at, updated_at) for audit trail

#### `database/session.py`
Provide:
- SQLAlchemy engine & session factory
- `init_db()` function to create all tables on startup
- Connection pooling (important for async scraping with Playwright)

#### `scraper/scraper_runner.py`
Core async scraper class:
- Constructor: `__init__(headless=True, max_pages=int)` 
- Method: `async run(category: dict)` - main scraping logic per category
- Responsibilities:
  - Launch browser via BrowserManager
  - Navigate to base_url + category search
  - Paginate results (respects max_pages)
  - Extract business data
  - Persist to database
  - Handle retries & rate-limiting

#### `scraper/browser_manager.py`
Playwright lifecycle manager:
- Context manager for browser/page
- Stealth mode configuration (already in requirements: playwright-stealth 2.0.3)
- Timeout & error handling
- Resource cleanup (critical for long-running async operations)

#### `utils/logger.py`
Centralized logging:
- Function: `build_logger()` returning a configured logger
- Format: Include timestamps, log level, module name
- Output: Console + file (for Docker container logs)
- Levels: DEBUG (dev), INFO (prod)

### Configuration

#### `config.yml` Structure
- `database.url`: PostgreSQL connection string (override via `DATABASE_URL` env var in Docker)
- `scraper.base_url`: Target website (paginasamarillas.es/search/)
- `categorie`: List of category dicts (name, description, image_url)

#### Environment Variables
Define in `.env` or docker-compose.yml:
- `DATABASE_URL`: PostgreSQL connection (overrides config.yml)
- `LOG_LEVEL`: DEBUG | INFO | WARNING (default: INFO)
- `SCRAPER_HEADLESS`: true | false (default: true)
- `SCRAPER_MAX_PAGES`: int (default: 3, from config)

### Testing Strategy
**Currently**: No tests. Add before production:
- Unit tests for parsers & data validation
- Integration tests for DB operations (use test database)
- Smoke tests for Playwright browser launch

Use pytest + fixtures. Run: `pytest tests/`

## Important Details

1. **Async/Await**: Entire flow is async. Playwright is async-first; ensure all database operations support async (consider asyncpg instead of psycopg2 if full async is needed later).

2. **Error Recovery**: Current code catches exceptions per category but doesn't retry. Consider exponential backoff for network errors.

3. **Rate Limiting**: Not implemented. paginasamarillas.es may block aggressive scraping. Add delays between requests & respect robots.txt.

4. **Database Credentials**: Hardcoded in config.yml. Move to environment variables before production.

5. **Playwright Stealth**: Already in requirements (playwright-stealth 2.0.3) but not configured. Pass to browser init in BrowserManager.

6. **Logging Level**: `build_logger()` exists but implementation unknown. Ensure it respects LOG_LEVEL env var.

## Common Workflows

### Adding a New Category
1. Edit `config.yml`: Add entry to `categorie` list with name, description, image_url
2. Run: `python run_scrapper.py` — automatically picks up new category

### Debugging a Scrape Failure
1. Set `LOG_LEVEL=DEBUG` env var
2. Run scraper and check logs for parser errors
3. Use `headless=False` in ScraperRunner to see browser visually
4. Inspect HTML in page.content() before parsing

### Deploying to Production
1. Ensure `.env` has production DATABASE_URL & credentials
2. Build image: `docker build -t scrapper-spain:latest .`
3. Push to registry & deploy
4. Verify database migrations run on startup (implement flask_migrate)

## Known Gaps (MVP → Production)

| Item | Priority | Effort |
|------|----------|--------|
| Implement database models & session | Critical | 2h |
| Implement scraper_runner core logic | Critical | 4h |
| Add Playwright browser manager | Critical | 2h |
| Add HTML parsers for data extraction | Critical | 3h |
| Move secrets to environment variables | High | 1h |
| Add database migrations (Flask-Migrate) | High | 1.5h |
| Implement retry logic & rate-limiting | High | 2h |
| Add unit & integration tests | High | 4h |
| Add production logging & monitoring | Medium | 2h |
| API endpoints (Flask routes) if needed | Medium | 3h |
| Documentation (API, deployment) | Medium | 2h |

## Debugging Tips

- **Playwright hangs**: Check browser resource limits, increase timeout in browser_manager
- **DB connection errors**: Verify PostgreSQL is running; check DATABASE_URL in config or env
- **Parser errors**: Enable DEBUG logging, inspect HTML structure changes in target website
- **Config not loading**: Ensure config.yml is in same directory as run_scrapper.py
