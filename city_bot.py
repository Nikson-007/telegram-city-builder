import os
import logging
import time
import math
from aiogram.types import Message
from events import get_random_event
from middlewares import LoadCityMiddleware
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
import asyncio
import random
from aiogram import html
from classes import Street, City, Building
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import BUILDING_CONFIG, GAME_SETTINGS
from DataBase import init_db, update_balance, update_happiness, destroy_building_in_bd, save_building_to_db, update_city_name, update_user_tax, update_user_stats, update_db_structure, get_user_ui, set_user_ui, get_last_tax_time, update_tax_time, get_user_rank, claim_bonus, get_top_players, upgrade_building_in_db, add_user, get_user_money, add_street, count_streets, get_full_city_data, update_user_money, add_building_to_db

class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    green = "\x1b[32;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record=record)
    

handler_console = logging.StreamHandler()
handler_console.setFormatter(CustomFormatter())

handler_file = logging.FileHandler("city_bot.log")
handler_file.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler_console, handler_file]
)


logger = logging.getLogger(__name__)


load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode='Markdown')
)
dp = Dispatcher()
router = Router()
'''@dp.message()
async def debug_handler(message: types.Message):
    print(f"Пришло сообщение: {message.text}")
    # Не удаляй этот хэндлер пока не проверишь, 
    # печатает ли он текст кнопки при нажатии.'''
user_cities = {}
user_cities.clear()

ADVISOR_PHRASES = {
    "tax": [
        "💰 Казна пополнилась! Жители ворчат, но платят.",
        "📈 Экономика города показывает стабильный рост, сэр!",
        "💼 Инспекторы проверили отчеты — всё чисто. Деньги в казне.",
        "🏦 Ваши сейфы становятся теснее от золота!"
    ],
    "build": [
        "🏗 Фундамент заложен! Скоро здесь закипит жизнь.",
        "🏢 Отличный выбор места, господин мэр!",
        "🧱 Кирпич за кирпичом — так строятся империи.",
        "🏗 Новое здание украсит облик нашего города!"
    ],
    "zero_profit": [
        "🦗 В казне пусто... Может, пора что-нибудь построить?",
        "📉 Налогов нет. Жители живут в коробках из-под холодильников!",
        "💨 В сейфах только перекати-поле. Нужно больше зданий!"
    ]
}

RANDOM_EVENTS = [
    {
        "name": "🎭 Городской фестиваль",
        "effect": 1.5, # Увеличивает собранные налоги в 1.5 раза
        "msg": "В городе прошел масштабный фестиваль! Туристы оставили кучу денег. Доход увеличен!"
    },
    {
        "name": "🌧 Проливные дожди",
        "effect": 0.7, # Снижает доход
        "msg": "Из-за ливней торговля встала, а дороги подмыло. Доход сегодня чуть ниже обычного."
    },
    {
        "name": "🏢 Бизнес-форум",
        "effect": 1.2,
        "msg": "Инвесторы в восторге от вашей политики! Налоговые поступления выросли."
    },
    {
        "name": "🦹 Налет карманников",
        "effect": 0.9,
        "msg": "В торговых районах участились кражи. Часть налогов испарилась в неизвестном направлении."
    }
]

RARE_EVENTS = [
    {
        "name": "💎 Алмазная жила", 
        "effect": 10.0, 
        "msg": "При прокладке труб рабочие нашли алмазы! Доход х10!"
    },
    {
        "name": "🌋 Извержение вулкана", 
        "effect": 0.1, 
        "msg": "Катастрофа! Почти вся прибыль ушла на спасательные работы."
    },
    {
        "name": "🛸 Визит пришельцев", 
        "effect": 5.0, 
        "msg": "Инопланетяне закупились сувенирами на космическую сумму!"
    }
]





class BuildingState(StatesGroup):
    waiting_for_title = State()  # Для названия здания
    waiting_for_type = State()   # Для типа здания

class RoadCreation(StatesGroup):
    waiting_for_name = State()   # Для названия улицы
    waiting_for_length = State() # Для длины улицы

class CityStates(StatesGroup):
    waiting_for_city_name = State()


def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text='📊 Статистика'))
    builder.add(KeyboardButton(text='🗺 Посмотреть город'))
    builder.add(KeyboardButton(text='💰 Собрать налоги'))
    builder.add(KeyboardButton(text='🏗 Построить здание'))
    builder.add(KeyboardButton(text='🛣 Новая улица'))
    builder.add(KeyboardButton(text='🔝 Улучшить здание'))
    builder.add(KeyboardButton(text='🏆 Топ игроков'))
    builder.add(KeyboardButton(text='⚙️ Настройки'))
    builder.add(KeyboardButton(text="✏️ Изменить название города"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard = True)

def streets_inline_keyboard(city):
    builder = InlineKeyboardBuilder()
    
    for street in city.streets:
        # Проверяем: если это кортеж, достаем имя по индексу
        if isinstance(street, tuple):
            # Предположим, что в кортеже имя — это второй элемент (индекс 1)
            # А ID — первый элемент (индекс 0)
            s_name = street[1] 
            s_id = street[0]
        else:
            # Если это объект класса Street
            s_name = street.name
            s_id = street.db_id

        builder.button(
            text=f"🛣 {s_name}", 
            callback_data=f"view_street:{s_id}"
        )
    
    builder.adjust(1)
    return builder.as_markup()

def streets_build_keyboard(city: City):
    builder = InlineKeyboardBuilder()
    for street in city.streets:
        builder.add(InlineKeyboardButton(
            text=f"🏗 {street.name}", 
            callback_data=f"build_on_street:{street.db_id}")
        )
    builder.adjust(1)
    return builder.as_markup()


# Хэндлер на команду /start
@dp.message(Command('start'))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.full_name or f"Мэр {user_id}"
    
    await add_user(user_id=user_id, username=username)
    
    # Город уже загружен Middleware-ом в user_cities[user_id]
    city = user_cities.get(user_id) 

    # Если города нет даже после Middleware — значит, это совсем новый юзер
    if not city:
        city = City(money=1000)
        user_cities[user_id] = city

    await message.answer(
        f"С возвращением, господин мэр! 🏙\nВаш баланс: {city.money}$", 
        reply_markup=main_menu_keyboard()
    )

@dp.message(F.text == '⚙️ Настройки')
async def setting_menu(message: types.Message):
    await show_settings(message)

@dp.message(Command("settings"))
async def show_settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📱 По 1 в ряд (Смартфон)", callback_data="set_ui_1"))
    builder.add(InlineKeyboardButton(text="🖥 По 2 в ряд (ПК/Планшет)", callback_data="set_ui_2"))
    builder.add(InlineKeyboardButton(text="💰 Управление налогами", callback_data="manage_taxes"))
    builder.adjust(1)

    '''await message.answer(
        "⚙️ *Настройки интерфейса*\n\n"
        "Выберите, как бот должен выводить списки зданий для улучшения. "
        "Режим 'ПК' экономит место, а 'Смартфон' показывает полные названия.", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )'''
    await message.answer(
        "⚙️ *Настройки города*\n\n"
        "Здесь вы можете изменить интерфейс или настроить налоговую политику.", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )

async def get_tax_menu_content(city: City):
    """Вспомогательная функция для генерации контента налогового меню"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="➖ 1%", callback_data="change_tax_-1"))
    builder.add(InlineKeyboardButton(text="➕ 1%", callback_data="change_tax_1"))
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_settings"))
    builder.adjust(2, 1)

    tax_desc = "Нормальный"
    if city.tax_rate > 15: 
        tax_desc = "Гребите деньги лопатой (Люди в ярости) 😡"
    elif city.tax_rate < 10: 
        tax_desc = "Налоговая гавань (Люди счастливы) 🥰"

    text = (
        f"💰 *Налоговая политика*\n\n"
        f"Текущая ставка: *{city.tax_rate}%*\n"
        f"Статус: _{tax_desc}_\n\n"
        f"⚠ *Помни:* высокий налог увеличивает прибыль, но бьет по Счастью жителей."
    )
    return text, builder.as_markup()

@dp.callback_query(F.data == "manage_taxes")
async def tax_settings_menu(callback: types.CallbackQuery):
    city = user_cities.get(callback.from_user.id)
    if not city:
        return await callback.answer("Ошибка: город не найден")

    text, reply_markup = await get_tax_menu_content(city)
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("change_tax_"))
async def process_tax_change(callback: types.CallbackQuery):
    delta = int(callback.data.split("_")[-1]) # берем последний элемент
    city = user_cities.get(callback.from_user.id)
    
    if not city: return await callback.answer()

    new_rate = max(1, min(25, city.tax_rate + delta))
    
    if new_rate != city.tax_rate:
        city.tax_rate = new_rate
        await update_user_tax(callback.from_user.id, new_rate)
        
        # Обновляем текст и кнопки в текущем сообщении
        text, reply_markup = await get_tax_menu_content(city)
        try:
            await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except: 
            # На случай, если пользователь нажал слишком быстро и текст не изменился
            pass
    
    await callback.answer(f"Ставка: {city.tax_rate}%")

@dp.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📱 По 1 в ряд (Смартфон)", callback_data="set_ui_1"))
    builder.add(InlineKeyboardButton(text="🖥 По 2 в ряд (ПК/Планшет)", callback_data="set_ui_2"))
    builder.add(InlineKeyboardButton(text="💰 Управление налогами", callback_data="manage_taxes"))
    builder.adjust(1)

    await callback.message.edit_text(
        "⚙️ *Настройки города*\n\n"
        "Здесь вы можете изменить интерфейс или настроить налоговую политику.", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )
    await callback.answer()
    
@dp.callback_query(F.data.startswith("set_ui_"))
async def change(callback: types.CallbackQuery):
    layout = int(callback.data.split("_")[2])
    await set_user_ui(callback.from_user.id, layout)

    mode = "Смартфон (1 в ряд)" if layout == 1 else "ПК (2 в ряд)"
    await callback.answer(f"✅ Установлен режим: {mode}")
    await callback.message.edit_text(f"✅ Масштаб изменен! Теперь интерфейс настроен под: *{mode}*", 
                                     parse_mode="Markdown")

    
@dp.message(F.text == '❌ Отмена')
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_keyboard())


@dp.message(F.text == '🏆 Топ игроков')
async def show_leaderboard(message: types.Message):
    user_id = message.from_user.id
    top_list = await get_top_players()
    user_rank = await get_user_rank(user_id=user_id)


    if not top_list:
        await message.answer("Список лидеров пока пуст.")
        return

    text = "🏆 *Топ самых богатых мэров:*\n\n"
    text += "--- \n"

    for i, (name, money) in enumerate(top_list, 1):
        if name == message.from_user.full_name:
            text += f"\n*{i}. {name} — {money}$*"
        else:
            text += f"\n{i}. {name} — {money}$"

    text += "\n\n---"

    if user_rank:
        text += f"\n\n👤 *Ваше место: {user_rank}*"

    await message.answer(text, parse_mode="Markdown")



    
@dp.message(F.text == '📊 Статистика')
async def show_stats(message: types.Message):
    user_id = message.from_user.id
    city = user_cities.get(user_id)
    

    if not city:
        await message.answer("Сначала введите /start, чтобы основать город.")
        return
    
    xp_to_next = city.level * 100
    progress = int((city.xp / xp_to_next) * 10)
    bar = "🟦" * progress + "⬜" * (10 - progress)

    total_res = city.get_total_residents()
    total_jobs = city.get_total_jobs()
    income_per_minute = city.calculate_current_income()
    total_maintenance = sum(b.get_maintenance() for s in city.streets for b in s.slots if b)
    net_profit = income_per_minute - total_maintenance

    profit_emoji = "💵" if net_profit >= 0 else "🧨"

    status_emoji = "✅ Город процветает"
    if total_jobs > total_res:
        status_emoji = "⚠️ Нехватка рабочих рук!"
    elif total_res > total_jobs * 1.5:
        status_emoji = "📉 Высокая безработица"

    happiness = city.calculate_happiness()
    if happiness >= 80: happy_emoji = "😇 Счастлив"
    elif happiness >= 50: happy_emoji = "😐 Средне"
    else: happy_emoji = "😡 Злость"
    
    

    msg = (
        f"🏙 Город: *{city.name}*\n"
        f"---\n"
        f"👤 Мэр *{city.level} уровня *\n"
        f"🔋 {bar} ({city.xp}/{xp_to_next} XP)\n"
        f"---\n"
        f"💰 Бюджет: {city.money}$\n"
        f"📈 Валовый доход: +{income_per_minute}$/мин\n"
        f"📉 Расходы (ЖКХ): -{total_maintenance}$/мин\n"
        f"{profit_emoji} *Чистая прибыль: {net_profit}$/мин*\n"
        f"---\n"
        f"👥 Население: {total_res}\n"
        f"😊 Счастье жителей: {happiness}% ({happy_emoji})\n"
        f"🛠 Рабочих мест: {total_jobs}\n"
        f"🛣 Улиц в городе: {len(city.streets)}\n"
        f"🏗 Свободных мест: {city.empty_slots()}\n"
        f"---\n"
        f"Статус: {status_emoji}"
    )

    

    
    await message.answer(msg)

@dp.message(F.text == '🏗 Построить здание')
async def start_building_process(message: types.Message):
    user_id = message.from_user.id
    city = user_cities.get(user_id)

    if not city or not city.streets:
        await message.answer("У вас еще нет улиц! Сначала постройте хотя бы одну.")
        return
    
    await message.answer(
        "На какой улице будем строить?",
        reply_markup=streets_build_keyboard(city)
    )




@dp.message(F.text == '🗺 Посмотреть город')
async def view_city(message: types.Message):
    user_id = message.from_user.id
    
    # Изменяем имя переменной с city_data на city
    city = user_cities.get(user_id)
    
    if not city:
        await message.answer("🏙 *Ваш город пуст!*", parse_mode="Markdown")
        return

    # Теперь 'city' существует и код ниже будет работать
    news_banner = ""
    if random.random() < 0.20:
        events = [
            {"text": "🍎 Фермерский рынок! +500$", "money": 500, "emoji": "🎉"},
            {"text": "🚧 Ремонт трубы. -300$", "money": -300, "emoji": "🛠"}
        ]
        event = random.choice(events)
        city.money += event["money"]
        await update_user_money(user_id, city.money)
        news_banner = f"📢 *НОВОСТИ:* {event['emoji']} {event['text']}\n━━━━━━━━━━━━━━\n"

    header = (
        f"🏘 *ПАНОРАМА ГОРОДА: {city.name}*\n" # Теперь ошибка NameError исчезнет
        f"━━━━━━━━━━━━━━\n"
        f"{news_banner}"
        f"📍 Уровень мэра: `{city.level}`\n"
        f"😊 Счастье: `{city.calculate_happiness()}%` | 💰 Налог: `{city.tax_rate}%` \n"
        f"━━━━━━━━━━━━━━\n\n"
    )

    await message.answer(
        header, 
        reply_markup=streets_inline_keyboard(city),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("view_street:"))
async def handle_view_street(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    city = user_cities.get(user_id)
    
    # Получаем ID из callback_data
    street_id = int(callback.data.split(":")[1])
    
    # Находим нужную улицу по её ID
    street = next((s for s in city.streets if s.db_id == street_id), None)
    
    if not street:
        await callback.answer("Улица не найдена!", show_alert=True)
        return

    # Формируем текст конкретной улицы
    view = street.get_street_view()
    report = (
        f"🛣 *Улица: {street.name}*\n"
        f"━━━━━━━━━━━━━━\n"
        f"{view}\n\n"
        f"👥 Жителей: `{sum(b.residents for b in street.slots if b)}`"
    )

    # Кнопка назад
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu"))
    kb.add(InlineKeyboardButton(text="🔨Снести здание", callback_data=f"prepare_delete:{street_id}"))

    # edit_text вместо answer, чтобы сообщение обновилось!
    await callback.message.edit_text(report, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer() # Убирает "часики" с кнопки

@dp.callback_query(F.data == "back_to_main_menu")
async def back_to_city_menu(callback: types.CallbackQuery):
    # Просто вызываем заново функцию отображения города, но через edit_text
    user_id = callback.from_user.id
    city = user_cities.get(user_id)
    
    header = (
        f"🏘 *ПАНОРАМА ГОРОДА: {city.name}*\n" # Добавили имя города!
        f"━━━━━━━━━━━━━━\n"
        f"📍 Уровень мэра: `{city.level}`\n"
        f"😊 Счастье: `{city.calculate_happiness()}%` | 💰 Налог: `{city.tax_rate}%` \n"
        f"━━━━━━━━━━━━━━\n\n"
    )
    
    await callback.message.edit_text(
        header, 
        reply_markup=streets_inline_keyboard(city), 
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("prepare_delete:"))
async def delete_building(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    street_id = int(callback.data.split(":")[1])
    city = user_cities.get(callback.from_user.id)

    street = next((s for s in city.streets if s.db_id == street_id), None)

    if not street:
        await callback.answer("Улица не найдена!", show_alert=True)
        return
    
    occupied_slots = [i for i, b in enumerate(street.slots) if b is not None]

    if not occupied_slots:
        await callback.answer("На этой улице нет зданий для сноса!", show_alert=True)
        return
    
    index = max(occupied_slots)
    await destroy_building_in_bd(street_id, index)
    street.slots[index] = None

    city.xp = max(0, city.xp - 50) # Наказание за снос здания
    await update_user_stats(user_id=callback.from_user.id, xp=city.xp, level=city.level)

    message_text = (
        f"🏗 Здание на улице *{street.name}* успешно снесено!\n"
        f"📉 Штраф за снов: `-50 XP` (Текущий опыт: `{city.xp}`)"
    )

    await callback.message.edit_text(
        text=message_text,
        reply_markup=streets_inline_keyboard(city),
        parse_mode="Markdown"
    )
    await callback.answer()
    

@dp.message(F.text == '🛣 Новая улица')
async def start_road_creation(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    city = user_cities.get(user_id)

    if not city:
        await message.answer("У вас еще нет города! Введите /start.")
        return



    if len(city.streets) >= 20:
        await message.answer("🏛 Лимит улиц достигнут! Улучшайте текущие районы.")
        return

    await message.answer("Как мы назовем новую улицу?")
    await state.set_state(RoadCreation.waiting_for_name)


@dp.message(RoadCreation.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Теперь введите длину улицы (число):")
    await state.set_state(RoadCreation.waiting_for_length)

@dp.message(Command("cancel"))
@dp.message(F.text.casefold() == 'отмена')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действие отменено. Возвращаемся в главное меню.",
        reply_markup=main_menu_keyboard())

@dp.message(RoadCreation.waiting_for_length)
async def process_length(message: types.Message, state: FSMContext):
    
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите целое число для длины улицы.")
        return
    
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("⚠ Ошибка! Длина улицы должна быть целым положительным числом (например, 5).")
        return # Даем шанс исправиться
    
    length = int(message.text)
    if length > 20:
        await message.answer("🏗 Ого, это слишком длинная улица! Максимальная длина — 20.")
        return
    
    user_id = message.from_user.id

    data = await state.get_data()
    street_name = data.get("name")

    cost = length * 10
    city = user_cities.get(user_id)

    if city.money < cost:
        await message.answer(f"❌ Недостаточно средств! Нужно {cost}$, а у вас {city.money}$")
        await state.clear()
        return

    city.money -= cost # Вычитаем из памяти
    await update_user_money(user_id, city.money) # Сохраняем в базу

    '''============СОХРАНЕНИЕ============'''
    await add_street(user_id=user_id, name=street_name, length=length)

    city = user_cities.get(user_id)
    if city:
        city.streets.append(Street(name=street_name, length=length))

    await message.answer("Улица построена!", parse_mode="Markdown")
    await state.clear()

    if await claim_bonus(user_id, "road"):
        city.money += 500
        await update_user_money(user_id, city.money)
        await message.answer("🎉 *Грант получен!* Вы получили 500$ за строительство первой дороги!", parse_mode="Markdown")

@dp.callback_query(F.data.startswith('select_street_'))
async def street_selected(callback: types.CallbackQuery, state: FSMContext):
    street_index = int(callback.data.split('_')[2])

    await state.update_data(selected_street_index = street_index)

    await callback.message.edit_text(f"Выбрана улица. Теперь введите название здания:")
    # Переключаем на состояние ожидания НАЗВАНИЯ ЗДАНИЯ
    await state.set_state(BuildingState.waiting_for_title)

    await callback.answer()





    

@dp.message(F.text == "💰 Собрать налоги")
async def collect_taxes_handler(message: Message, city: City):
    if not city: return
    
    user_id = message.from_user.id
    income = city.calculate_current_income()
    
    if income <= 0:
        await message.answer(random.choice(ADVISOR_PHRASES["zero_profit"]))
        return

    city.money += income
    await update_user_money(user_id, city.money)
    
    xp_gain = GAME_SETTINGS.get('xp_per_collect', 10)
    await gain_exp(user_id, xp_gain, message)

    await message.answer(
        f"📊 **Налоги собраны!**\n"
        f"💵 Доход: `+{income}$`\n"
        f"😊 Счастье: `{city.calculate_happiness()}%`",
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("build_on_street:"))
async def process_build_on_street(callback: types.CallbackQuery, state: FSMContext):
    street_id = int(callback.data.split(":")[1])
    # Сохраняем ID улицы и находим первый пустой слот
    city = user_cities.get(callback.from_user.id)
    street = next((s for s in city.streets if s.db_id == street_id), None)
    
    slot_idx = street.get_first_free_slot()
    await state.update_data(street_id=street_id, slot_index=slot_idx)
    
    await callback.message.edit_text("🏗 Введите название для нового здания:")
    await state.set_state(BuildingState.waiting_for_title)
    await callback.answer()

@dp.message(BuildingState.waiting_for_title)
async def process_building_title(message: types.Message, state: FSMContext):
    # Сохраняем введенное название в память FSM
    await state.update_data(building_title=message.text)
    
    # Показываем типы зданий из твоего BUILDING_CONFIG
    builder = InlineKeyboardBuilder()
    for b_type, params in BUILDING_CONFIG.items():
        builder.add(InlineKeyboardButton(
            text=f"{params['icon']} {b_type} — {params['cost']}$", 
            callback_data=f"select_b_type:{b_type}")
        )
    builder.adjust(1)
    
    await message.answer("Отлично! Теперь выбери тип постройки:", reply_markup=builder.as_markup())
    await state.set_state(BuildingState.waiting_for_type)


@dp.callback_query(F.data.startswith("select_b_type:"))
async def finalize_building(callback: types.CallbackQuery, state: FSMContext):
    building_type = callback.data.split(":")[1]
    user_data = await state.get_data()
    
    street_id = user_data.get("street_id")
    slot_index = user_data.get("slot_index")
    title = user_data.get("building_title")

    if not title:
        return await callback.answer("Ошибка: название не найдено. Начните сначала.", show_alert=True)

    city = user_cities.get(callback.from_user.id)
    config = BUILDING_CONFIG.get(building_type)

    if city.money < config['cost']:
        return await callback.answer(f"Недостаточно средств! Нужно: {config['cost']} 💰", show_alert=True)

    # 1. Сначала обновляем локальный объект и списываем деньги
    city.money -= config['cost']
    new_building = Building(building_type, title)
    
    # 2. Обновляем состояние в памяти (чтобы сразу отобразилось в интерфейсе)
    street = next((s for s in city.streets if s.db_id == street_id), None)
    if street:
        street.slots[slot_index] = new_building

    # 3. Синхронизируем с БД (важные асинхронные вызовы)[cite: 32, 35]
    try:
        await save_building_to_db(callback.from_user.id, street_id, slot_index, new_building)
        await update_user_money(callback.from_user.id, city.money)
        
        await callback.message.edit_text(
            f"✅ **{title}** успешно построено!\n"
            f"Списано: {config['cost']} 💰\n"
            f"Остаток: {city.money} 💰"
        )
    except Exception as e:
        # Если БД упала, стоит хотя бы залогировать ошибку
        await callback.answer("Произошла ошибка при сохранении данных в БД", show_alert=True)
        print(f"Ошибка БД: {e}") 

    await state.clear()

@dp.callback_query(F.data.startswith("upgrade_street_"))
async def list_buildings_for_upgrade(callback: types.CallbackQuery):
    # Извлекаем индекс улицы из callback_data (upgrade_street_0, upgrade_street_1 и т.д.)
    street_index = int(callback.data.split("_")[2])
    
    user_id = callback.from_user.id
    city = user_cities.get(user_id)
    
    if not city or street_index >= len(city.streets):
        await callback.answer("Ошибка: улица не найдена", show_alert=True)
        return

    street = city.streets[street_index]
    builder = InlineKeyboardBuilder()
    
    has_buildings = False

    # Проходим по всем слотам на улице
    for slot_idx, building in enumerate(street.slots):
        if building:
            has_buildings = True
            # Считаем стоимость следующего уровня
            cost = building.get_upgrade_cost()
            
            # Текст кнопки: [Иконка] Название (Ур. L -> L+1) — Цена$
            # Например: 🏠 Жилой дом (1 ➔ 2) — 300$
            button_text = f"{building.name} ({building.level} ➔ {building.level + 1}) — {cost}$"
            
            # Передаем в callback индексы улицы и слота, чтобы знать, что именно качать
            builder.add(InlineKeyboardButton(
                text=button_text, 
                callback_data=f"upg_exec_{street_index}_{slot_idx}")
            )

    if not has_buildings:
        await callback.answer("На этой улице пока нет зданий!", show_alert=True)
        return

    # Кнопка возврата к выбору улиц
    builder.add(InlineKeyboardButton(text="⬅️ Назад к улицам", callback_data="back_to_upgrade_streets"))
    
    builder.adjust(1) # Делаем список в одну колонку для удобства чтения цен

    await callback.message.edit_text(
        f"🏗 *Улучшение зданий: ул. {street.name}*\n\n"
        f"💰 Ваш баланс: *{city.money}$*\n"
        f"Выбранное здание получит бонус к доходу и вместимости.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("upg_exec_"))
async def execute_upgrade(callback: types.CallbackQuery):
    # Разбираем callback_data (upg_exec_ИНДЕКС_УЛИЦЫ_ИНДЕКС_СЛОТА)
    data_parts = callback.data.split("_")
    s_idx = int(data_parts[2])
    b_idx = int(data_parts[3])
    
    user_id = callback.from_user.id
    city = user_cities[user_id]
    street = city.streets[s_idx]
    building = street.slots[b_idx]
    
    cost = building.get_upgrade_cost()
    
    if city.money >= cost:
        city.money -= cost
        building.level += 1  # Уровень вырос -> свойства income/residents/jobs выросли сами
        
        # Обновляем БД (деньги мэра)
        await update_user_money(user_id, city.money)
        
        # Обновляем БД (уровень конкретного здания)
        # Передаем db_id улицы, индекс слота и новый уровень
        await upgrade_building_in_db(street.db_id, b_idx, building.level)
        
        await callback.answer(
            f"🚀 {building.name} улучшен до уровня {building.level}!\n"
            f"📈 Теперь доход: {building.income}$", 
            show_alert=True
        )
        
        # Перерисовываем меню апгрейдов, чтобы обновить цены и описание
        await list_buildings_for_upgrade(callback)
    else:
        await callback.answer(f"⚠️ Недостаточно денег! Нужно: {cost}$", show_alert=True)

@dp.callback_query(F.data == "back_to_upgrade_streets")
async def back_to_upgrade_streets(callback: types.CallbackQuery):
    await start_upgrade_selection(callback.message) # Вызываем начальный хэндлер
    await callback.answer()

@dp.message(F.text == '🔝 Улучшить здание')
async def start_upgrade_selection(message: types.Message):
    user_id = message.from_user.id
    city = user_cities.get(user_id)

    if not city or not city.streets:
        await message.answer("У вас еще нет улиц со зданиями!")
        return

    builder = InlineKeyboardBuilder()
    for index, street in enumerate(city.streets):
        builder.add(InlineKeyboardButton(
            text=f"🏙 {street.name}", 
            callback_data=f"upgrade_street_{index}")
        )
    builder.adjust(1)

    await message.answer("Выберите улицу, на которой хотите улучшить здание:", 
                         reply_markup=builder.as_markup())
    
async def notify_admin_error(error_message: str):
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, f"🚨 *ОШИБКА В БОТЕ:*\n\n`{error_message}`", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу: {e}")

async def gain_exp(user_id, amount, message: types.Message):
    city = user_cities.get(user_id)
    if not city: return
    
    city.xp += amount
    xp_needed = city.level * 100

    leveled_up = False

    while city.xp >= xp_needed:
        city.xp -= xp_needed
        city.level += 1
        xp_needed = city.level * 100
        leveled_up = True

    if leveled_up:
        unlocked = []
        for b_name, params in BUILDING_CONFIG.items():
            if params.get('min_level') == city.level:
                unlocked.append(b_name)

        msg_text = (
            f"🎉 *УРОВЕНЬ ПОВЫШЕН!*\n"
            f"Теперь вы мэр *{city.level} уровня*! 🏛\n"
        )
        
        if unlocked:
            buildings_list = "\n".join([f"— {b}" for b in unlocked])
            msg_text += f"\n🔓 *Новые постройки:*\n{buildings_list}"
        
        await message.answer(msg_text, parse_mode="Markdown")

    await update_user_stats(user_id, city.xp, city.level)


# 1. Срабатывает при нажатии на кнопку
# Исправленный кусок (строка 750+)
@dp.message(F.text == "✏️ Изменить название города")
async def rename_city_call(message: types.Message, state: FSMContext):
    await message.answer("📝 Введите новое название для вашего города:")
    await state.set_state(CityStates.waiting_for_city_name)

# 2. Ловит текстовое сообщение с новым названием
@dp.message(CityStates.waiting_for_city_name)
async def rename_city_finish(message: types.Message, state: FSMContext):
    new_name = message.text
    user_id = message.from_user.id
    city = user_cities.get(user_id)

    if city:
        city.name = new_name
        # ОБЯЗАТЕЛЬНО добавь это, чтобы в БД сохранилось:
        await update_city_name(user_id, new_name) 
        
        await message.answer(f"✅ Город успешно переименован в **{new_name}**!", parse_mode="Markdown")
    else:
        await message.answer("❌ Ошибка: Город не найден.")
    
    await state.clear()
        




async def main():
    logger.info("Запуск процесса инициализации БД...")
    try:
        await init_db()
        await update_db_structure()
        logger.info("БД успешно инициализирована, таблицы проверены/созданы.")
        
        dp.callback_query.outer_middleware(LoadCityMiddleware(user_cities, get_full_city_data))
        dp.message.outer_middleware(LoadCityMiddleware(user_cities, get_full_city_data))
        logger.info("Middleware запущен и полностью исправен.")
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА при инициализации БД: {e}")
        return # Если база не создалась, дальше запускать бота нет смысла

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)








if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен.')