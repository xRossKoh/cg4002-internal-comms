from bluno_beetle_udp import BlunoBeetleUDP

import constant

imu_sensor = BlunoBeetleUDP((3, constant.P1_IMU_SENSOR))
#mu_sensor = BlunoBeetleUDP((3, constant.P2_IMU_SENSOR))
imu_sensor.start()
