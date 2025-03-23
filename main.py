import asyncio
import sqlalchemy as db
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from structures import *
import sqlite3
import aiosqlite
from headers import *
from telbot import main_bot

engine = create_async_engine(url='sqlite+aiosqlite:///db.enerkotik.sqlite3')
async_session = async_sessionmaker(engine, class_=AsyncSession)
conn = engine.connect()
meta = db.MetaData()

async def scrap():
    debug_info = await magnit.scrape()
    print(debug_info)
    # debug_info = await perekrestok.scrape()
    # print(debug_info)

async def create_tables():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

async def main():
    await create_tables()
    await scrap()
    await main_bot()


if __name__ == '__main__':
    asyncio.run(main())

