import random

EVENTS = [
    {
        "name": "🔥 Пожар в жилом секторе!",
        "desc": "Из-за старой проводки начался пожар. Счастье падает, казна пустеет на ремонт.",
        "money_change": -2000,
        "happiness_change": -10,
        "chance": 0.3 # Вес события
    },
    {
        "name": "💰 Щедрый инвестор",
        "desc": "Миллионер из соседнего мегаполиса решил открыть у вас филиал!",
        "money_change": 5000,
        "happiness_change": 5,
        "chance": 0.2
    },
    {
        "name": "🎭 Городской фестиваль",
        "desc": "Жители в восторге! Счастье растет, но организация стоила денег.",
        "money_change": -1000,
        "happiness_change": 15,
        "chance": 0.5
    }
]

def get_random_event():
    if random.random() < 0.15: # 15% шанс, что событие вообще произойдет
        return random.choices(EVENTS, weights=[e["chance"] for e in EVENTS])[0]
    return None