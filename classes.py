import datetime






class Building:
    def __init__(self, name, b_type, income, residents, jobs=0, level=1) -> None:
        self.name = name
        self.b_type = b_type
        self.base_income = income
        self.base_residents = residents
        self.base_jobs = jobs
        self.level = level

    @property
    def income(self):
        return int(self.base_income * (1 + (self.level - 1) * 0.5))
    
    @property
    def residents(self):
        return int(self.base_residents * (self.level**1.1))
    
    @property
    def jobs(self):
        return int(self.base_jobs * (self.level**1.2))
    
    def get_upgrade_cost(self):
        return (self.base_income * 20) * self.level
    
    def get_maintenance(self):
        base_maintenance = self.income * 0.2
        return int(base_maintenance * (1 + (self.level - 1) * 0.5))



class Street:
    def __init__(self, name, length: int, db_id: int = None) -> None:
        self.name = name
        self.slots = [None for i in range(length)]
        self.db_id = db_id


    def occupy_slot(self, slot_index, building_object):
        if 0 <= slot_index < len(self.slots):
            self.slots[slot_index] = building_object
        else:
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
                icon = icons.get(slot.b_type, "🏗")
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
    
class City:
    def __init__(self, money, level=1, xp=0, streets: list = None, tax_rate = 10, name = None) -> None:
        self.money = money
        self.streets = streets if streets else []
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
                    if b.b_type == '🏭 Завод': factories += 1
                    if b.b_type == '🌳 Парк': parks += 1
                    if b.b_type == '🏥 Больница': hospitals += 1

        happiness = base_happiness + tax_impact + (parks * 10) + (hospitals * 5) - (factories * 10)

        total_res = self.get_total_residents()
        total_jobs = self.get_total_jobs()
        if total_res > total_jobs * 1.5:
            happiness -= 15

        return max(0, min(100, happiness))