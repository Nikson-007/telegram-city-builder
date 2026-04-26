from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Awaitable
from classes import City, Street, Building

class LoadCityMiddleware(BaseMiddleware):
    def __init__(self, user_cities: dict, get_full_city_data_func) -> None:
        self.user_cities = user_cities
        self.get_full_city_data = get_full_city_data_func
        super().__init__()

    async def __call__(
            self, 
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],  
            event: Message | CallbackQuery, 
            data: Dict[str, Any]
            ) -> Any:
        
        user_id = event.from_user.id

        if user_id not in self.user_cities:
            city_data = await self.get_full_city_data(user_id)
            if city_data:
                city = City(money=city_data['money'],
                            level=city_data['level'],
                            xp=city_data['xp'],
                            tax_rate=city_data.get('tax_rate', 13))
                for s_id, s_info in city_data["streets"].items():
                    new_street = Street(
                        name=s_info["name"], 
                        length=s_info["length"], 
                        db_id=s_id
                    )
                    for b_info in s_info["buildings"]:
                        new_building = Building(
                            name=b_info["name"], b_type=b_info["type"],
                            income=b_info["income"], residents=b_info["residents"],
                            jobs=b_info.get("jobs", 0), level=b_info.get("level", 1)
                        )
                        new_street.occupy_slot(b_info["slot"], new_building)
                    city.streets.append(new_street)
                self.user_cities[user_id] = city

        return await handler(event, data)

