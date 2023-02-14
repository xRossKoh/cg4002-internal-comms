from bluno_beetle_udp import BlunoBeetleUDP

imu_sensor = BlunoBeetleUDP((3, "c4:be:84:20:19:4c"))
imu_sensor.bluno_beetle_main()
