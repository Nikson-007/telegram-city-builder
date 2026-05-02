import datetime
from config import BUILDING_CONFIG






import datetime
from config import BUILDING_CONFIG

class Building:
    def __init__(self, b_type: str, custom_name: str = None, level: int = 1):
        config = BUILDING_CONFIG.get(b_type)
        if not config:
            raise ValueError(f"Тип здания {b_type} не найден в конфиге")

        self.type = b_type # Используем это имя везде
        self.name = custom_name or b_type
        self.level = level
        
        # Базовые значения из конфига для расчетов
        self._base_income = config['income']
        self._base_residents = config['residents']
        self._base_jobs = config['jobs']

    @property
    def income(self):
        return int(self._base_income * (self.level**1.2))

    @property
    def residents(self):
        return int(self._base_residents * (self.level**1.1))

    @property
    def jobs(self):
        return int(self._base_jobs * (self.level**1.2))

    def get_upgrade_cost(self):
        base_cost = BUILDING_CONFIG[self.type]['cost']
        return int(base_cost * 1.5 * self.level)

    def get_maintenance(self):
        return int((self.income * 0.2) * (1 + (self.level - 1) * 0.5))
    def upgrade(self):
        self.level += 1



class Street:
    def __init__(self, name, length: int, db_id: int = None) -> None:
        self.name = name
        self.length = length
        self.db_id = db_id
        self.buildings = []
        self.slots = [None] * length


    def occupy_slot(self, slot_index, building):
        if 0 <= slot_index < len(self.slots):
            self.slots[slot_index] = building
            return True
        return False

    def get_street_view(self) -> str:
        from config import BUILDING_CONFIG # Импорт внутри, чтобы избежать циклической зависимости
        
        view = []
        for slot in self.slots:
            if slot is None:
                view.append("⬜")
            else:
                # Берем иконку прямо из конфига по типу здания
                params = BUILDING_CONFIG.get(slot.type, {})
                icon = params.get('icon', "🏗")
                
                lvl_superscript = {1: "", 2: "²", 3: "³", 4: "⁴", 5: "⁵"}.get(slot.level, f"^{slot.level}")
                view.append(f"{icon}{lvl_superscript}")
        return " ".join(view)
    
    def add_building(self, building_object) -> bool:
        for i in range(len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = building_object
                return i
        return None
    
    # В классе Street
    def get_first_free_slot(self):
        for i, slot in enumerate(self.slots):
            if slot is None:
                return i
        return None
    
class City:
    def __init__(self, money, level=1, xp=0, streets: list = None, tax_rate = 13, name = None) -> None:
        self.money = money
        # ВАЖНО: просто сохраняем список, не меняя его тип!
        self.streets = streets if streets is not None else []
        self.level = level
        self.xp = xp
        self.tax_rate = tax_rate
        self.name = name

    def show_stats(self):
        income = 0
        residents = 0
        print(f'Бюджет города: {self.money}')
        for street in self.streets:
            for build in street.slots:
                if build != None:
                    residents += build.residents
                    income += build.income

        print(f'Доход города составляет: {income}')
        print(f'Общее количество жителей города: {residents}')
        for street in self.streets:
            print(street.get_street_view())

    def empty_slots(self) -> int:
        count = 0
        for street in self.streets:
            for build in street.slots:
                if build is None:
                    count += 1 
        return count
    
    def collect_taxes(self):
        income = 0
        for street in self.streets:
            for build in street.slots:
                if build != None:
                    income += build.income

        self.money += income

    def get_total_residents(self):
        return sum(b.residents for s in self.streets for b in s.slots if b)
    
    def get_total_jobs(self):
        return sum(b.jobs for s in self.streets for b in s.slots if b)
    
    def calculate_current_income(self):
        base_income = sum(b.income for s in self.streets for b in s.slots if b)
        return int(base_income * (self.tax_rate / 10))
    
    def calculate_happiness(self):
        base_happiness = 50
        factories = 0
        parks = 0
        
        for street in self.streets:
            for b in street.slots:
                if b is None: continue
                if b.type == '🏭 Завод': # Проверяй именно b.type
                    factories += 1
                elif b.type == '🌳 Парк':
                    parks += 1
                    
        # Логика: заводы уменьшают счастье, парки увеличивают
        total_happiness = base_happiness - (factories * 10) + (parks * 15)
        return max(0, min(100, total_happiness)) # Ограничение от 0 до 100