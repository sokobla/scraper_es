from playwright.async_api import async_playwright
from playwright_stealth import Stealth

class BrowserFactory:
    def __init__(self, headless=True):
        self.headless = headless
        self._stealth_cm = None
        self._playwright = None

    async def launch(self):
        self._stealth_cm = Stealth().use_async(async_playwright())
        self._playwright = await self._stealth_cm.__aenter__()

        browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            locale="fr-FR",
            timezone_id="Europe/Paris",
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()
        return browser, context, page

    async def shutdown(self, browser, context):
        if context:
            await context.close()
        if browser:
            await browser.close()
        if self._stealth_cm:
            await self._stealth_cm.__aexit__(None, None, None)