class GameState:
    def __init__(self):
        self.ammo = 6
        self.health = 100

    @property
    def ammo(self):
        return self.ammo

    @property
    def health(self):
        return self.health

    @ammo.setter
    def ammo(self, updated_ammo):
        self.ammo = updated_ammo

    @health.setter
    def health(self, updated_health):
        self.health = updated_health
