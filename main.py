from controller import Controller

controller = Controller([
    (1, "c4:be:84:20:1a:51"),   # P1 gun (IR transmitter)
    (2, "b0:b1:13:2d:d6:37"),   # P1 vest (IR receiver)
    (3, "c4:be:84:20:19:4c"),   # P1 glove (IMU and flex sensors)
    #(4, ""),                   # P2 gun (IR transmitter)
    #(5, ""),                   # P2 vest (IR receiver)
    #(6, "")                    # P2 glove (IMU and flex sensors)
])
controller.run_threads()
