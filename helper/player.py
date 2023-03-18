from bluno_beetle import BlunoBeetle
from bluno_beetle_udp import BlunoBeetleUDP
from bluno_beetle_game_state import BlunoBeetleGameState
from game_state import GameState

class Player:
    def __init__(self, params):
        self.gun = BlunoBeetleGameState(params[0])
        self.vest = BlunoBeetleGameState(params[1])
        self.glove = BlunoBeetleUDP(params[2])
        self.game_state = GameState()
