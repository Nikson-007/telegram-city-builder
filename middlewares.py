from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from classes import City

class LoadCityMiddleware(BaseMiddleware):
    def __init__(self, user_cities: dict, get_full_city_data_func) -> None:
        self.user_cities = user_cities
        self.get_data = get_full_city_data_func
        super().__init__()

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user:
            # Пытаемся достать город из БД
            city = await self.get_data(user.id)
            
            # Если в БД города нет (новый игрок), создаем пустой объект City
            # Это предотвратит ошибку AttributeError в хэндлерах
            if not city:
                city = City(money=1000) 
            
            # Обновляем оперативную память и прокидываем в хэндлер
            self.user_cities[user.id] = city
            data["city"] = city
            
        return await handler(event, data)