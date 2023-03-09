from bluno_beetle import BlunoBeetle

import constant

ir_receiver = BlunoBeetle((2, constant.P1_IR_RECEIVER))
#ir_receiver = BlunoBeetle((5, constant.P2_IR_RECEIVER))
ir_receiver.start()
