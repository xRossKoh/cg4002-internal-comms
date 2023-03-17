class GameState:
    def __init__(self):
        self._bullets = 6
        self._health = 100

    @property
    def bullets(self):
        return self._bullets

    @property
    def health(self):
        return self._health

    @bullets.setter
    def bullets(self, updated_bullets):
        self._bullets = updated_bullets

    @health.setter
    def health(self, updated_health):
        self._health = updated_health
