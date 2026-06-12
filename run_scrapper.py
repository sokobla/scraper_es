import asyncio
from pathlib import Path
import yaml

from database.session import init_db, wait_for_db, close_db
from scraper.scraper_runner import ScraperRunner
from utils.logger import build_logger

logger = build_logger()

def load_categories_from_config(config_path: str = "config.yml") -> list[dict]:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path.resolve()}")

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    categories = config.get("categorie", [])

    if not isinstance(categories, list):
        raise ValueError("config.yml: 'categorie' must be a list")

    normalized = []
    for item in categories:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        if not name:
            continue

        normalized.append({
            "name": name,
            "description": item.get("description"),
            "image": item.get("image"),
        })

    return normalized

async def main():
    # 🔥 Wait for PostgreSQL to be ready BEFORE trying to initialize
    logger.info("⏳ Waiting for PostgreSQL to be ready...")
    await wait_for_db()

    # Now safe to create tables
    init_db()
    categories = load_categories_from_config("config.yml")

    if not categories:
        logger.info("Aucune catégorie trouvée dans config.yml")
        return

    logger.info(f"{len(categories)} catégorie(s) chargée(s) depuis config.yml")

    runner = ScraperRunner(headless=True, max_pages=999)

    for index, category in enumerate(categories, start=1):
        logger.info("-" * 80)
        logger.info(f"[{index}/{len(categories)}] Catégorie={category['name']}")
        logger.info(f"Description={category.get('description')}")
        logger.info(f"Image={category.get('image')}")

        try:
            await runner.run(category=category)
            logger.info(f"[OK] Scraping terminé pour {category['name']}")
        except Exception as exc:
            logger.error(f"[ERROR] Échec scraping pour {category['name']}: {exc}")

    # 🔥 Clean up database connections
    close_db()
    logger.info("✅ Application terminée avec succès")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")
        close_db()
        exit(1)