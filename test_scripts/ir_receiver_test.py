import sys

# importing necessary module directories
sys.path.append('/home/kenneth/Desktop/CG4002/scripts/bluno_beetle')
sys.path.append('/home/kenneth/Desktop/CG4002/scripts/helper')

from bluno_beetle_game_state import BlunoBeetleGameState

import constant

ir_receiver = BlunoBeetleGameState((2, constant.P2_IR_RECEIVER))
#ir_receiver = BlunoBeetle((5, constant.P2_IR_RECEIVER))
ir_receiver.start()
