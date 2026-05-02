from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from classes import City

class LoadCityMiddleware(BaseMiddleware):
    def __init__(self, user_cities: dict, get_full_city_data_func) -> None:
        # Передаем словарь и функцию загрузки из основного файла
        self.user_cities = user_cities
        self.get_full_city_data = get_full_city_data_func
        super().__init__()

    async def __call__(
            self, 
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],  
            event: Message | CallbackQuery, 
            data: Dict[str, Any]
            ) -> Any:
        
        # Получаем ID пользователя из сообщения или колбэка
        user_id = event.from_user.id

        # Если данных о городе нет в оперативной памяти (словаре)
        if user_id not in self.user_cities:
            # Вызываем твою функцию get_full_city_data (которая теперь возвращает объекты)
            city_data = await self.get_full_city_data(user_id)
            
            if city_data:
                # Создаем экземпляр City. Так как в city_data['streets'] уже лежат 
                # объекты Street, City инициализируется правильно.
                self.user_cities[user_id] = City(**city_data)
            else:
                # Если игрока нет в БД, здесь можно оставить None или 
                # создать стартовый город, если это предусмотрено логикой
                pass 

        # Важно: пробрасываем объект города в data, чтобы его можно было 
        # достать в хэндлере вот так: async def handler(msg, city: City)
        data['city'] = self.user_cities.get(user_id)

        return await handler(event, data)