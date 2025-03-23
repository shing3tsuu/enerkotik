import bs4
import pendulum
from datetime import datetime
from datetime import date
from sqlalchemy import select, func
from dataclasses import dataclass
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, expect
import requests
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
import sqlalchemy as db
from structures import Products

engine = create_async_engine(url='sqlite+aiosqlite:///db.enerkotik.sqlite3')
async_session = async_sessionmaker(engine, class_=AsyncSession)
conn = engine.connect()
meta = db.MetaData()

@dataclass
class ScraperConfig:
    main_class: str
    main_link: str
    name_class: str
    name_link: str
    cost_class: str
    cost_link: str


@dataclass
class ConnectionParams:
    headers: dict
    cookies: dict
    params: dict


class ShopScraper:
    def __init__(
        self,
        name: str,
        link: str,
        connection_params: ConnectionParams,
        scraper_config: ScraperConfig,
        website_method: str,
        debug_info: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.link = link
        self.connection_params = connection_params
        self.scraper_config = scraper_config
        self.website_method = website_method
        self.debug_info = debug_info or {}
        self.utc_date = self._get_current_date()

    @staticmethod
    def _get_current_date() -> date:
        utc_date = date.today()
        return utc_date

    @staticmethod
    def _clean_price(price_str: str) -> int:
        return int(price_str.replace('Цена', '').split(".")[0].split(",")[0].strip())

    async def _process_element(self, element, session):
        try:
            name_element = element.find(
                self.scraper_config.name_class,
                class_=self.scraper_config.name_link
            )
            if not name_element:
                return None

            element_name = name_element.text.strip()
            cost_element = element.find(
                self.scraper_config.cost_class,
                class_=self.scraper_config.cost_link
            )
            element_cost = self._clean_price(cost_element.text) if cost_element else 0

            await self._update_database(
                session=session,
                name=element_name,
                cost=element_cost
            )

            return element_name, element_cost

        except Exception as e:
            self.debug_info.setdefault('errors', []).append(str(e))
            return None

    async def _update_database(self, session, name: str, cost: int):
        existing = await session.scalar(
            select(Products).filter_by(
                name=name,
                shop=self.name,
                update_date=self.utc_date
            )
        )

        if not existing:
            session.add(Products(
                name=name,
                cost=cost,
                shop=self.name,
                update_date=self.utc_date
            ))
        else:
            existing.cost = cost

    async def scrape(self):
        if self.website_method == 'dynamic':
            return await self._dynamic_scrape()
        return await self._static_scrape()

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

    async def _process_pages_dynamic(self, page, pages: int = 2):
        for page_num in range(1, pages + 1):
            current_link = self._update_page_number(page_num)
            await page.goto(current_link)
            await page.wait_for_timeout(3000)

            content = await page.content()
            await self._parse_content(content)

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
            finally:
                self.debug_info['status_code'] = response.status_code
                content = response.text
                await self._parse_content(content)

            return await self._finalize_debug_info()

    def _update_page_number(self, page_num: int) -> str:
        return self.link.replace('=1', f'={page_num}')

    async def _parse_content(self, content: str):
        soup = bs4.BeautifulSoup(content, features="html.parser")
        elements = soup.find_all(
            self.scraper_config.main_class,
            class_=self.scraper_config.main_link
        )
        async with async_session() as session:
            for idx, element in enumerate(elements, 1):
                result = await self._process_element(element, session)
                if result:
                    self.debug_info['element_number'] = idx
                    await session.commit()
                else:
                    self.debug_info['element_status'] = False
                    break

    async def _finalize_debug_info(self):
        count = await self._get_element_count()
        self.debug_info['session_elements_count'] = count
        return self.debug_info

    async def _get_element_count(self) -> int:
        utc_date = self._get_current_date()
        async with async_session() as session:
            return (await session.execute(select(func.count(Products.id))
            .filter(Products.shop == self.name, Products.update_date == utc_date))).scalar()

    @property
    def debug_info(self):
        return self._debug_info

    @debug_info.setter
    def debug_info(self, value):
        self._debug_info = value