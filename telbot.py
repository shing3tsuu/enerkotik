import logging
from typing import Awaitable
import emoji
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums import ParseMode
import sqlalchemy as db
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from botconfig import load_config
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, BigInteger, select, not_
import pendulum
import matplotlib.pyplot as plt
import io
from aiogram.types import BufferedInputFile
from structures import *


async def create_plot(dates: list, costs: list) -> BufferedInputFile:
    plt.figure(figsize=(12, 7))
    plt.style.use('ggplot')
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.plot(
        dates,
        costs,
        marker='o',
        linestyle='--',
        color='#2c7be5',
        linewidth=2,
        markersize=8
    )

    plt.title("Динамика цен", fontsize=14, pad=20)
    plt.xlabel("Дата", fontsize=12, labelpad=15)
    plt.ylabel("Цена, RUB", fontsize=12, labelpad=15)

    plt.grid(True, linestyle='--', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return BufferedInputFile(
        file=buf.getvalue(),
        filename="price_trend.png"
    )


async def get_products_name(session: AsyncSession, name: str, page: int) -> tuple[list, bool]:
    offset = page * 5
    update_date = date.today()

    if name.lower() == 'найти все':
        name = 'нер'

    query = (
        select(Products)
        .where(
            Products.name.ilike(f"%{name}%"),
            Products.update_date == update_date
        )
        .offset(offset)
        .limit(6)
    )

    result = await session.scalars(query)
    elements = result.all()
    return elements[:5], len(elements) > 5


async def get_products_cost(session: AsyncSession, cost: int, page: int) -> tuple[list, bool]:
    offset = page * 5
    update_date = date.today()
    low_cost = cost - 10
    high_cost = cost + 10

    query = (
        select(Products)
        .filter(
            Products.cost.between(low_cost, high_cost),
            Products.update_date == update_date
        )
        .offset(offset)
        .limit(6)
    )

    result = await session.scalars(query)
    elements = result.all()
    return elements[:5], len(elements) > 5


async def get_plot_data(session: AsyncSession, name: str) -> tuple[list, list]:

    product = await session.scalar(select(Products)
        .where(
            Products.name.ilike(f"%{name}%")
        )
    )

    result = await session.scalars(select(Products)
        .where(
            Products.name.ilike(f"%{product.name}%"),
            Products.shop == f'{product.shop}'
        )
        .order_by(Products.update_date.asc()))

    elements = result.all()

    dates = [elem.update_date for elem in elements]
    costs = [elem.cost for elem in elements]

    return dates, costs, product.name


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(self, handler: Callable[[Message, Dict[str | Any, Any]], Awaitable[Any]],
                             event: Message, data: Dict[str | Any, Any]) -> Any:
        async with self.session_pool() as session:
            data['session'] = session
            try:
                return await handler(event, data)
            except Exception as e:
                await session.rollback()
                logger.error(f'Database error: {e}')
                raise
            finally:
                await session.close()

class States(StatesGroup):
    name = State()
    plot_name = State()
    cost = State()
    page = State()
    has_next = State()

async def main_bot():
    config = load_config(".env")
    engine = create_async_engine(url='sqlite+aiosqlite:///db.enerkotik.sqlite3')
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.update.middleware(DatabaseMiddleware(session_pool=session_factory))

    dp.include_router(router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


def create_main_keyboard():
    builder = ReplyKeyboardBuilder()
    buttons = [
        'Поиск по названию',
        'Поиск по цене',
        'Динамика цен'
    ]
    for text in buttons:
        builder.add(types.KeyboardButton(text=text))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


async def build_pagination_keyboard_name(current_page: int, has_next: bool) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    if current_page > 0:
        builder.button(
            text=emoji.emojize(":left_arrow:"),
            callback_data="back_name"
        )
    if has_next:
        builder.button(
            text=emoji.emojize(":right_arrow:"),
            callback_data="next_name"
        )
    builder.adjust(3 if has_next and current_page > 0 else 2)

    return builder


async def build_pagination_keyboard_cost(current_page: int, has_next: bool) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    if current_page > 0:
        builder.button(
            text=emoji.emojize(":left_arrow:"),
            callback_data="back_cost"
        )
    if has_next:
        builder.button(
            text=emoji.emojize(":right_arrow:"),
            callback_data="next_cost"
        )
    builder.adjust(3 if has_next and current_page > 0 else 2)

    return builder


def format_answer(elements: list, page: int) -> str:
    if not elements:
        return "😔 Ничего не найдено"

    items = [f"• {elem.name} - {elem.cost} руб. ({elem.shop})" for elem in elements]
    return (
            "🔍 Результаты поиска:\n" +
            "\n".join(items) +
            f"\n\nСтраница: {page + 1}"
    )

router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()

    answer = f'Привет, <b> {message.from_user.full_name} </b>, я твой личный котенок для поиска прокдутов из магазина, подскажу цену, ее динамику, где этот товар найти и актуальные скидки'

    user = await session.scalar(select(Users).filter_by(tg_id=message.from_user.id))
    if not user:
        try:
            new_user = Users(tg_id=message.from_user.id, name=message.from_user.full_name)
            session.add(new_user)
            await message.answer(answer, reply_markup=create_main_keyboard())
        except Exception as e:
            await message.answer("Попробуйте позже")
            logger.error(f"User creation error: {e}")
    else:
        await message.answer(answer, reply_markup=create_main_keyboard())


@router.message(F.text == 'Назад')
async def cmd_back(message: Message, state: FSMContext, session: AsyncSession):
    await cmd_start(message, state, session)

@router.message(F.text == 'Поиск по названию')
async def cmd_find_name(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    await state.set_state(States.name)
    await state.update_data(page=0, has_next=False)

    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text='Назад'))

    await message.answer(
        'Я буду искать товары по названию. Примеры запросов:\n'
        '• Найти все → Я покажу все товары, что есть в наличии\n'
        '• burn → Burn, Burn Energy\n'
        '• tor → Tornado\n'
        '• gORI → Gorilla (регистр не важен)',
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@router.message(States.name)
async def process_name(message: Message, state: FSMContext, session: AsyncSession):
    try:
        await state.update_data(name=message.text.strip(), page=0)
        data = await state.get_data()

        elements, has_next = await get_products_name(
            session=session,
            name=data['name'],
            page=data['page']
        )

        await state.update_data(has_next=has_next)
        builder = await build_pagination_keyboard_name(data['page'], has_next)

        await message.answer(
            format_answer(elements, data['page']),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer("🚨 Произошла ошибка")

@router.callback_query(F.data.in_(['next_name', 'back_name']))
async def handle_pagination_name(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        await callback.answer()
        data = await state.get_data()

        page = data.get('page', 0)
        new_page = page + 1 if callback.data == 'next_name' else max(0, page - 1)

        elements, has_next = await get_products_name(
            session=session,
            name=data['name'],
            page=new_page
        )

        await state.update_data(page=new_page, has_next=has_next)
        builder = await build_pagination_keyboard_name(data['page'], has_next)

        await callback.message.edit_text(
            text=format_answer(elements, new_page),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Pagination error: {e}")
        await callback.answer("⚠️ Ошибка обновления", show_alert=True)

@router.message(F.text == 'Поиск по цене')
async def cmd_find_cost(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    await state.set_state(States.cost)
    await state.update_data(page=0, has_next=False)

    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text='Назад'))

    await message.answer('Я буду искать товары для тебя по цене, можешь написать любое число,'
                         ' и я найду все товары, что приближены по цене к нему, например: 70 = 60-80',
                         reply_markup=builder.as_markup(resize_keyboars=True))

@router.message(States.cost)
async def process_cost(message: Message, state: FSMContext, session: AsyncSession):
    try:
        await state.update_data(cost=message.text.strip(), page=0)
        data = await state.get_data()

        elements, has_next = await get_products_cost(
            session=session,
            cost=int(data['cost']),
            page=data['page']
        )

        await state.update_data(has_next=has_next)
        builder = await build_pagination_keyboard_cost(data['page'], has_next)

        await message.answer(
            format_answer(elements, data['page']),
            reply_markup=builder.as_markup(),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer("🚨 Произошла ошибка")

@router.callback_query(F.data.in_(['next_cost', 'back_cost']))
async def handle_pagination_cost(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        await callback.answer()
        data = await state.get_data()\

        page = data.get('page', 0)
        new_page = page + 1 if callback.data == 'next_cost' else max(0, page - 1)

        elements, has_next = await get_products_cost(
            session=session,
            cost=int(data['cost']),
            page=new_page
        )

        await state.update_data(page=new_page, has_next=has_next)
        builder = await build_pagination_keyboard_cost(data['page'], has_next)

        await callback.message.edit_text(
            text=format_answer(elements, new_page),
            reply_markup=builder.as_markup(),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Pagination error: {e}")
        await callback.answer("⚠️ Ошибка обновления", show_alert=True)


@router.message(F.text == 'Динамика цен')
async def cmd_find_plot(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    await state.set_state(States.plot_name)
    await state.update_data(page=0, has_next=False)

    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text='Назад'))

    await message.answer(
        'Я буду искать товары по названию и генерировать для них динамику цен:\n'
        'Пиши названия точнее, если хочешь найти определенный товар\n'
    )


@router.message(States.plot_name)
async def handle_plot_request(message: types.Message,
                              state: FSMContext,
                              session: AsyncSession):
    try:
        user_input = message.text.strip()
        if not user_input:
            await message.answer("🔍 Пожалуйста, введите название товара")
            return

        await state.update_data(plot_name=user_input)
        data = await state.get_data()

        dates, costs, product_name = await get_plot_data(
            session=session,
            name=data['plot_name']
        )

        if not costs or len(costs) < 2:
            await message.answer("📊 Недостаточно данных для построения графика")
            return

        photo = await create_plot(dates, costs)
        await message.answer_photo(
            photo=photo,
            caption=f"График цен для: {product_name}"
        )

    except Exception as e:
        logger.error(f"Plot error: {str(e)}", exc_info=True)
        await message.answer("🚨 Произошла ошибка при генерации графика")