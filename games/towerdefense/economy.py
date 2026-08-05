class Economy:
    def __init__(self, gold: int = 200, gems: int = 0):
        self.gold = gold
        self.gems = gems

    def spend(self, amount: int) -> bool:
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def earn_gold(self, amount: int):
        self.gold += amount

    def earn_gems(self, amount: int):
        self.gems += amount

    def can_afford(self, amount: int) -> bool:
        return self.gold >= amount
