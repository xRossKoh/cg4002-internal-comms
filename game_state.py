class GameState:
    def __init__(self):
        self._ammo = 6
        self._health = 100

    @property
    def ammo(self):
        return self._ammo

    @property
    def health(self):
        return self._health

    @ammo.setter
    def ammo(self, updated_ammo):
        self._ammo = updated_ammo

    @health.setter
    def health(self, updated_health):
        self._health = updated_health
