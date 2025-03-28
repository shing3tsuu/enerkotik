from contextlib import asynccontextmanager
from pkgutil import get_data
from typing import AsyncGenerator, Optional, Dict, Any
import bs4
import requests
import logging
from playwright.async_api import async_playwright
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from parsing_scheme import ShopScraperSchema, ConnectionParamsSchema, ScraperConfigSchema
from structures import User, Product, Shop
from botconfig import load_config
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from datetime import date


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

config = load_config(".env")
engine = create_async_engine(
    url=f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:{config.db.port}/{config.db.name}",
    pool_size=5,
    max_overflow=5,
    echo=False
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# session factory with async context manager
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            async with session.begin():
                yield session
        except Exception as e:
            logger.error(f"Database error: {e}", exc_info=True)
            raise

# main class to scrape
class ShopScraper(ShopScraperSchema):
    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def _clean_price(price_str: str) -> int:
        try:
            return int(price_str.replace('Цена', '').split(".")[0].split(",")[0].strip())
        except (ValueError, AttributeError):
            return 0

    def _update_page_number(self, page_num: int) -> str:
        return self.link.replace('=1', f'={page_num}')

    @staticmethod
    def _get_current_date() -> date:
        return date.today()

    async def scrape(self):
        if self.website_method == 'dynamic':
            return await self._dynamic_scrape()
        elif self.website_method == 'static':
            return await self._static_scrape()
        else:
            raise ValueError("Invalid website_method. Supported methods are 'dynamic' and 'static'.")

    async def _update_database(self, name: str, cost: int):
        async with get_session() as session:
            try:
                shop = await session.scalar(select(Shop).filter_by(name=self.shop_name))
                if not shop:
                    shop = Shop(name=self.shop_name)
                    session.add(shop)
                    await session.commit()

                product = await session.scalar(
                    select(Product).filter_by(
                        name=name,
                        shop_id=shop.id,
                        update_date=self._get_current_date()
                    )
                )
                if product:
                    product.cost = cost
                else:
                    session.add(Product(
                        name=name,
                        cost=cost,
                        shop_id=shop.id,
                        update_date=self._get_current_date()
                    ))
                await session.commit()
            except Exception as e:
                logger.error(f"Database update failed: {e}", exc_info=True)
                await session.rollback()
                raise


    async def _finalize_debug_info(self):
        async with get_session() as session:
            self.debug_info['element_count'] = await session.scalar(
                select(func.count(Product.id)).filter_by(shop_id=Shop.id, update_date=self._get_current_date())
            )
        return self.debug_info


    async def _get_element_count(self) -> int:
        async with get_session() as session:
            result = await session.execute(
                select(func.count(Product.id)).filter(
                    Products.shop_id == self.shop.id,
                    Products.update_date == self._get_current_date()
                )
            )
            return result.scalar()

    async def _process_element(self, element: bs4.element.Tag) -> Optional[tuple]:
        try:
            name_element = element.find(
                self.scraper_config.name_class,
                class_=self.scraper_config.name_link
            )
            if not name_element:
                return None

            cost_element = element.find(
                self.scraper_config.cost_class,
                class_=self.scraper_config.cost_link
            )

            return (
                name_element.text.strip(),
                self._clean_price(cost_element.text) if cost_element else 0
            )
        except Exception as e:
            logger.error(f"Element processing error: {e}", exc_info=True)
            self.debug_info.setdefault('errors', []).append(str(e))
            return None


    async def _parse_content(self, content: str):
        soup = bs4.BeautifulSoup(content, "html.parser")
        elements = soup.find_all(
            self.scraper_config.main_class,
            class_=self.scraper_config.main_link
        )

        for idx, element in enumerate(elements, 1):
            if result := await self._process_element(element):
                await self._update_database(*result)
                self.debug_info['processed_elements'] = idx
            else:
                self.debug_info['element_status'] = False
                raise ValueError("Element processing failed.")


    async def _dynamic_scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                channel='chrome',
                headless=False,
                args=["--start-maximized"]
            )
            try:
                context = await browser.new_context(no_viewport=True)
                page = await context.new_page()
                await self._process_pages_dynamic(page)
            finally:
                await browser.close()
        return await self._finalize_debug_info()


    async def _static_scrape(self, pages: int = 5):
        for page_num in range(1, pages + 1):
            current_link = self._update_page_number(page_num)
            try:
                response = requests.get(
                    current_link,
                    headers=self.connection_params.headers,
                    cookies=self.connection_params.cookies,
                    params=self.connection_params.params
                )
                self.debug_info['status_code'] = response.status_code
                await self._parse_content(response.text)
            except Exception as e:
                logger.error(f"Request failed: {e}")
                self.debug_info.setdefault('errors', []).append(str(e))

        return await self._finalize_debug_info()
