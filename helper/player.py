from bluno_beetle import BlunoBeetle
from bluno_beetle_udp import BlunoBeetleUDP
from bluno_beetle_game_state import BlunoBeetleGameState
from game_state import GameState

import threading

class Player(threading.Thread):
    # arr of GameState objs to keep track of game state for all players
    # to be instantiated in main.py
    players_game_state = []


    def __init__(self, params):
        self.player_id = params[0]
        self.beetles = [    BlunoBeetleGameState(params[0] + params[1]),    # gun (IR transmitter)
                            BlunoBeetleGameState(params[0] + params[2]),    # vest (IR receiver)
                            BlunoBeetleUDP(params[0] + params[3])]          # glove (imu_sensor)
        
    def set_game_state(self, new_bullets, new_health):
        players_game_state[self.player_id].bullets(new_bullets)
        players_game_state[self.player_id].health(new_health)

    def print_player_stats(self):
        print("Player {} - Bullets = {}, Health = {}".format(
            self.player_id,
            Player.players_game_state[self.player_id].bullets,
            Player.players_game_state[self.player_id].health,
        ))

    def print_player_beetle_info(self):
        for beetle in self.beetles:
            beetle.print_beetle_info

    def run(self):
        pass
