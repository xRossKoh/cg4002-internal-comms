from bluno_beetle import BlunoBeetle

import constant

ir_transmitter = BlunoBeetle((1, constant.P1_IR_TRANSMITTER))
#ir_transmitter = BlunoBeetle((4, constant.P2_IR_TRANSMITTER))
ir_transmitter.start()
