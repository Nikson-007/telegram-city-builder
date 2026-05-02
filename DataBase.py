import aiosqlite
import os
import datetime
import random
from classes import Street, Building, City

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'city_bot.db')

CITY_PREFIXES = ["Ново", "Старо", "Верхне", "Санкт-", "Нижне", "Зелено"]
CITY_ROOTS = ["град", "бург", "поль", "горск", "ск", "сити"]


random_name = random.choice(CITY_PREFIXES) + random.choice(CITY_ROOTS)


print(f"DEBUG: Путь к базе данных: {DB_NAME}")

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        # таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                money INTEGER DEFAULT 1000,
                ui_layout INTEGER DEFAULT 1,
                last_tax_collection TEXT,
                bonus_road_claimed INTEGER DEFAULT 0,
                bonus_build_claimed INTEGER DEFAULT 0
            )
        ''')
        # таблица улиц
        await db.execute('''
            CREATE TABLE IF NOT EXISTS streets(
                street_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                length INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        # таблица зданий
        await db.execute('''
            CREATE TABLE IF NOT EXISTS buildings(
                building_id INTEGER PRIMARY KEY AUTOINCREMENT,
                street_id INTEGER,
                name TEXT,
                type TEXT,
                income INTEGER,
                residents INTEGER,
                jobs INTEGER,
                slot_index INTEGER,
                level INTEGER DEFAULT 1,
                FOREIGN KEY (street_id) REFERENCES streets (street_id)
            )
        ''')
        
        await db.commit()


async def add_user(user_id, username):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username, money, city_name) VALUES (?, ?, ?, ?)',
            (user_id, username, 1000, random_name)
        )
        await db.commit()

async def get_user_money(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT money FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
    
async def add_street(user_id, name, length):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'INSERT INTO streets (user_id, name, length) VALUES (?, ?, ?)',
            (user_id, name, length)
        )
        await db.commit()

async def count_streets(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM streets WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
        
async def get_full_city_data(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        # 1. Данные города
        async with db.execute(
            "SELECT money, level, xp, city_name, tax_rate FROM users WHERE user_id = ?", 
            (user_id,)
        ) as cursor:
            city_row = await cursor.fetchone()
        
        if not city_row: return None

        # 2. Улицы
        async with db.execute(
            "SELECT street_id, name, length FROM streets WHERE user_id = ?", 
            (user_id,)
        ) as cursor:
            streets_rows = await cursor.fetchall()

        streets = []
        for s_row in streets_rows:
            street = Street(name=s_row[1], length=s_row[2], db_id=s_row[0])
            
            # 3. Здания для каждой улицы
            async with db.execute(
                "SELECT type, name, level, slot_index FROM buildings WHERE street_id = ?", 
                (s_row[0],)
            ) as b_cursor:
                buildings_rows = await b_cursor.fetchall()
                for b_row in buildings_rows:
                    building = Building(b_type=b_row[0], custom_name=b_row[1], level=b_row[2])
                    street.slots[b_row[3]] = building
            streets.append(street)

        return City(
            money=city_row[0], level=city_row[1], xp=city_row[2], 
            name=city_row[3], tax_rate=city_row[4], streets=streets
        )
    
async def add_building_to_db(user_id, street_name, name, b_type, income, residents, slot, jobs):
    async with aiosqlite.connect(DB_NAME) as db:
        # Сначала находим ID улицы по её названию и владельцу
        async with db.execute(
            "SELECT street_id FROM streets WHERE user_id = ? AND name = ?", 
            (user_id, street_name)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                street_id = row[0]
                # Теперь вставляем все 7 колонок (building_id и level заполнятся сами)
                await db.execute("""
                    INSERT INTO buildings (street_id, name, type, income, residents, jobs, slot_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (street_id, name, b_type, income, residents, jobs, slot))
                await db.commit()

async def update_user_money(user_id, money):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET money = ? WHERE user_id = ?", (money, user_id))
        await db.commit()

async def upgrade_building_in_db(street_id, slot_index, new_level):
    """
    Обновляет уровень здания в базе данных.
    Использует street_id и slot_index для точного поиска.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE buildings 
            SET level = ? 
            WHERE street_id = ? AND slot_index = ?
        """, (new_level, street_id, slot_index))
        await db.commit()

async def get_top_players(limit=20):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            'SELECT city_name, money FROM users ORDER BY money DESC LIMIT ?', # Сортируем по деньгам
            (limit,)
        ) as cursor:
            return await cursor.fetchall()
        
async def claim_bonus(user_id, bonus_type):
    async with aiosqlite.connect(DB_NAME) as db:
        column = "bonus_road_claimed" if bonus_type == "road" else "bonus_build_claimed"
        
        async with db.execute(f'SELECT {column} FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] == 0:
                await db.execute(f'UPDATE users SET money = money + 500, {column} = 1 WHERE user_id = ?', (user_id,))
                await db.commit()
                return True
        return False
    
async def get_user_rank(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT money FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            user_money = row[0]

        async with db.execute('SELECT COUNT(*) FROM users WHERE money > ?', (user_money,)) as cursor:
            row = await cursor.fetchone()
            rank = row[0] + 1
            return rank
        
async def save_building_to_db(user_id, street_id, slot_index, building):
    """
    Сохраняет новое здание в базу данных.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO buildings (street_id, name, type, income, residents, jobs, level, slot_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                street_id, 
                building.name, 
                building.type, 
                building.income, 
                building.residents, 
                building.jobs, 
                building.level, 
                slot_index
            )
        )
        await db.commit()
        
async def update_tax_time(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        now = datetime.datetime.now().isoformat()
        await db.execute('UPDATE users SET last_tax_collection = ? WHERE user_id = ?', (now, user_id))
        await db.commit()

async def get_last_tax_time(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT last_tax_collection FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None
        
async def set_user_ui(user_id, layout):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET ui_layout = ? WHERE user_id = ?', (layout, user_id))
        await db.commit()

async def get_user_ui(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT ui_layout FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 1
        
async def update_db_structure():
    async with aiosqlite.connect(DB_NAME) as db:
        # 1. Список колонок для таблицы пользователей (users)
        # Формат: (таблица, колонка, тип_и_дефолт)
        user_columns = [
            ("users", "xp", "INTEGER DEFAULT 0"),
            ("users", "level", "INTEGER DEFAULT 1"),
            ("users", "ui_layout", "INTEGER DEFAULT 1"),
            ("users", "bonus_road_claimed", "INTEGER DEFAULT 0"),
            ("users", "bonus_build_claimed", "INTEGER DEFAULT 0"),
            ("users", "happiness", "INTEGER DEFAULT 50"),
            ("users", "tax_rate", "INTEGER DEFAULT 13"),
            ("users", "city_name", "TEXT DEFAULT 'Мой город'")
        ]

        # 2. Список колонок для таблицы зданий (buildings)
        building_columns = [
            ("buildings", "jobs", "INTEGER DEFAULT 0"),
            ("buildings", "level", "INTEGER DEFAULT 1")
        ]

        # Объединяем всё в один цикл для чистоты кода
        all_updates = user_columns + building_columns

        for table, col_name, col_type in all_updates:
            try:
                # Пытаемся добавить колонку
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                print(f"DEBUG: Колонка {col_name} успешно добавлена в таблицу {table}.")
            except aiosqlite.OperationalError as e:
                # Если ошибка содержит "duplicate column name", значит колонка уже есть — это нормально
                if "duplicate column name" in str(e).lower():
                    pass 
                else:
                    print(f"DEBUG: Ошибка при обновлении таблицы {table}: {e}")
        
        await db.commit()

def get_xp_for_level(level):
    return level * 100

async def add_xp(user_id, amount, user_cities):
    city = user_cities.get(user_id)
    if not city: return

    city.xp += amount
    xp_needed = get_xp_for_level(city.level)

    leveled_up = False
    while city.xp >= xp_needed:
        city.xp -= xp_needed
        city.level += 1
        xp_needed = get_xp_for_level(city.level)
        leveled_up = True

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET xp = ?, level = ? WHERE user_id = ?",
            (city.xp, city.level, user_id)
        )
        await db.commit()
    return leveled_up

async def update_user_stats(user_id, xp, level):
    """Специальная функция для синхронизации опыта и уровня"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET xp = ?, level = ? WHERE user_id = ?",
            (xp, level, user_id)
        )
        await db.commit()

async def update_user_tax(user_id, tax_rate):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET tax_rate = ? WHERE user_id = ?", (tax_rate, user_id))
        await db.commit()

async def update_city_name(user_id, city_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET city_name = ? WHERE user_id = ?", (city_name, user_id))
        await db.commit()

async def destroy_building_in_bd(street_id, slot_index):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""DELETE FROM buildings WHERE street_id = ? AND slot_index = ?""", (street_id, slot_index))

        await db.commit()

async def update_balance(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET money = money + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def update_happiness(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET happiness = MAX(0, MIN(100, happiness + ?)) WHERE user_id = ?", 
            (amount, user_id)
        )
        await db.commit()