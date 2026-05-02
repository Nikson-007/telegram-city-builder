import datetime






class Building:
    def __init__(self, name, b_type, income, residents, jobs=0):
        self.name = name
        self.type = b_type
        
        # Храним базовые значения в "защищенных" переменных
        self._base_income = income 
        self._base_residents = residents
        self._base_jobs = jobs
        
        self.level = 1

    @property
    def income(self):
        # Используем базу для расчетов
        return int(self._base_income * (self.level**1.2))

    @property
    def residents(self):
        return int(self._base_residents * (self.level**1.1))

    @property
    def jobs(self):
        return int(self._base_jobs * (self.level**1.2))
    

    
    def get_upgrade_cost(self):
        return (self.base_income * 20) * self.level
    
    def get_maintenance(self):
        base_maintenance = self.income * 0.2
        return int(base_maintenance * (1 + (self.level - 1) * 0.5))



class Street:
    def __init__(self, name, length: int, db_id: int = None) -> None:
        self.name = name
        self.length = length
        self.db_id = db_id
        self.buildings = []
        self.slots = [None] * length


    def occupy_slot(self, slot_index, building):
        # Та самая строка 47, которая выдавала ошибку
        if 0 <= slot_index < len(self.slots):
            self.slots[slot_index] = building
            return True
        return False

    def get_street_view(self) -> str:
        icons = {
            '🏠 Жилой дом': '🏠',
            '🏭 Завод': '🏭',
            '🛒 Магазин': '🛒',
            '🌳 Парк': '🌳',
            '🚨 Полиция': '🚨',
            '🏥 Больница': '🏥',
            '👨‍🚒 Пожарные': '👨‍🚒',
            '🏛 Ратуша': '🏛'
        }

        view = []
        for slot in self.slots:
            if slot is None:
                view.append("⬜")
            else:
                icon = icons.get(slot.type, "🏗")
                # Если уровень > 1, добавляем маленькую цифру (надстрочную)
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
    def __init__(self, money, level=1, xp=0, streets: list = None, tax_rate = 10, name = None) -> None:
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
        tax_impact = (13 - self.tax_rate) * 5

        factories = 0
        parks = 0
        hospitals = 0
        for s in self.streets:
            for b in s.slots:
                if b:
                    if b.type == '🏭 Завод': factories += 1
                    if b.type == '🌳 Парк': parks += 1
                    if b.type == '🏥 Больница': hospitals += 1

        happiness = base_happiness + tax_impact + (parks * 10) + (hospitals * 5) - (factories * 10)

        total_res = self.get_total_residents()
        total_jobs = self.get_total_jobs()
        if total_res > total_jobs * 1.5:
            happiness -= 15

        return max(0, min(100, happiness))