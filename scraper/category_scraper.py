from urllib.parse import quote_plus
import re

from utils.logger import build_logger

logger = build_logger()


class ContactScraper:
    def __init__(self, page):
        self.page = page

    def attach_browser_console(self):
        self.page.on(
            "console",
            lambda msg: logger.info(f"[browser-console][{msg.type}] {msg.text}")
        )

    def build_search_url(self, category_name: str, page_number: int = 1) -> str:
        slug = quote_plus(category_name.strip().lower())
        return (
            f"https://www.paginasamarillas.es/search/"
            f"{slug}/all-ma/all-pr/all-is/all-ci/all-ba/all-pu/all-nc/{page_number}"
            f"?what={slug}&qc=true"
        )

    def normalize_text(self, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = re.sub(r"\s+", " ", value).strip()
        return cleaned or None

    async def safe_inner_text(self, locator) -> str | None:
        try:
            count = await locator.count()
            if count == 0:
                return None

            text = await locator.first.inner_text(timeout=2000)
            return self.normalize_text(text)
        except Exception:
            return None

    async def reveal_phone(self, card, category_name: str, page_number: int, card_index: int) -> str | None:
        phone_locator = card.locator('[itemprop="telephone"]')
        existing_phone = await self.safe_inner_text(phone_locator)
        if existing_phone:
            return existing_phone

        show_phone_trigger = card.locator(".showPhone")
        trigger_count = await show_phone_trigger.count()

        if trigger_count == 0:
            logger.info(
                f"[{category_name}] [page {page_number}] "
                f"[fiche {card_index}] Aucun bouton showPhone"
            )
            return None

        try:
            await show_phone_trigger.first.click(timeout=5000)
        except Exception as exc:
            logger.warning(
                f"[{category_name}] [page {page_number}] "
                f"[fiche {card_index}] Clic showPhone impossible: {exc}"
            )
            return None

        try:
            await self.page.wait_for_function(
                """
                (card) => {
                    const phoneNode = card.querySelector('[itemprop="telephone"]');
                    if (!phoneNode) return false;

                    const text = (phoneNode.textContent || '').trim();
                    const hiddenParent = phoneNode.closest('.hidden, .d-none');

                    return text.length > 0 && !hiddenParent;
                }
                """,
                arg=await card.element_handle(),
                timeout=5000,
            )
        except Exception:
            logger.info(
                f"[{category_name}] [page {page_number}] "
                f"[fiche {card_index}] Téléphone non révélé après attente"
            )

        return await self.safe_inner_text(phone_locator)

    async def extract_card_data(self, card, category: dict, page_number: int, card_index: int, page_url: str) -> dict | None:
        category_name = category.get("name", "unknown")

        name = await self.safe_inner_text(card.locator('[itemprop="name"]'))
        street = await self.safe_inner_text(card.locator('[itemprop="streetAddress"]'))
        postal_code = await self.safe_inner_text(card.locator('[itemprop="postalCode"]'))
        city = await self.safe_inner_text(card.locator('[itemprop="addressLocality"]'))
        phone = await self.reveal_phone(card, category_name, page_number, card_index)

        if not any([name, street, postal_code, city, phone]):
            logger.info(
                f"[{category_name}] [page {page_number}] "
                f"[fiche {card_index}] Fiche vide ignorée"
            )
            return None

        logger.info(
            f"[{category_name}] [page {page_number}] [fiche {card_index}] "
            f"nom={name!r} ville={city!r} cp={postal_code!r} tel={phone!r}"
        )

        return {
            "source": "paginasamarillas",
            "title": name[:255] if name else "Sans nom",
            "url": page_url,
            "score": None,
            "nom": name,
            "rue": street,
            "code_postal": postal_code,
            "ville": city,
            "telephone": phone,
            "raw_payload": {
                "category": category_name,
                "page_number": page_number,
                "nom": name,
                "rue": street,
                "code_postal": postal_code,
                "ville": city,
                "telephone": phone,
            },
        }

    async def scrape_category(self, category: dict, max_pages: int = 1) -> list[dict]:
        category_name = category.get("name", "unknown")
        all_results = []

        for page_number in range(1, max_pages + 1):
            url = self.build_search_url(category_name, page_number)
            logger.info(f"[{category_name}] Navigation vers page {page_number}: {url}")

            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)

            cards_locator = self.page.locator(".listado-item")
            await cards_locator.first.wait_for(state="attached", timeout=10000)

            cards = await cards_locator.all()
            logger.info(
                f"[{category_name}] Fiches détectées page {page_number}: {len(cards)}"
            )

            for index, card in enumerate(cards, start=1):
                try:
                    item = await self.extract_card_data(
                        card=card,
                        category=category,
                        page_number=page_number,
                        card_index=index,
                        page_url=url,
                    )
                    if item:
                        all_results.append(item)
                except Exception as exc:
                    logger.warning(
                        f"[{category_name}] [page {page_number}] "
                        f"[fiche {index}] Extraction ignorée: {exc}"
                    )

        logger.info(
            f"[{category_name}] Extraction terminée: {len(all_results)} résultats"
        )
        return all_results