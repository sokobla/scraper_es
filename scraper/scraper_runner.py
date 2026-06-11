from scraper.browser_factory import BrowserFactory
from scraper.category_scraper import ContactScraper
from services.result_service import ResultService
from utils.logger import build_logger

logger = build_logger()

class ScraperRunner:
    def __init__(self, headless=True, max_pages=1):
        self.headless = headless
        self.max_pages = max_pages
        self.result_service = ResultService()

    async def run(self, category: dict):
        logger.info(f"Démarrage scraping catégorie={category.get('name')}")
        factory = BrowserFactory(headless=self.headless)
        browser = None
        context = None

        try:
            browser, context, page = await factory.launch()

            scraper = ContactScraper(page)
            scraper.attach_browser_console()

            items = await scraper.scrape_category(
                category=category,
                max_pages=self.max_pages
            )

            saved = self.result_service.save_many(category=category, items=items)

            logger.info(
                f"Fin scraping catégorie={category.get('name')} | "
                f"extraits={len(items)} | enregistrés={len(saved)}"
            )
            return saved
        except Exception as exc:
            logger.exception(f"Erreur critique catégorie={category.get('name')}: {exc}")
            raise
        finally:
            await factory.shutdown(browser, context)
            logger.info(f"Ressources navigateur libérées catégorie={category.get('name')}")