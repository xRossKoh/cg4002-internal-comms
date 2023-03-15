from bluno_beetle import BlunoBeetle
from bluno_beetle_game_state import BlunoBeetleGameState

import constant

#ir_transmitter = BlunoBeetle((1, constant.P1_IR_TRANSMITTER))
#ir_transmitter = BlunoBeetle((4, constant.P2_IR_TRANSMITTER))
ir_transmitter = BlunoBeetleGameState((1, constant.P2_IR_RECEIVER))
ir_transmitter.start()
