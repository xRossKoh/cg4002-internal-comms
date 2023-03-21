import sys

# importing necessary module directories
sys.path.append('/home/kenneth/Desktop/CG4002/scripts/bluno_beetle')
sys.path.append('/home/kenneth/Desktop/CG4002/scripts/helper')

from bluno_beetle_udp import BlunoBeetleUDP

import constant

imu_sensor = BlunoBeetleUDP([0, 3, constant.P1_IMU_SENSOR])
#mu_sensor = BlunoBeetleUDP((3, constant.P2_IMU_SENSOR))
imu_sensor.start()
