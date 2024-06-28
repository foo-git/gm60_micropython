from gm60_micropython import GM60_Driver

# UART port/naming hint:
# GM60 RX (green cable) needs to be connected to ESP32 TX (e.g. here pin 25)
# GM60 TX (yellow cable) needs to be connected to ESP32 RX (e.g. here pin 26)
scanner = GM60_Driver(rx=26, tx=25)  # initialize UART connection to GM60 barcode scanner

scanner.get_version()  # prints hardware and software version information

scanner.reset_to_factory_defaults()  # resets scanner back to factory settings

scanner.get_register_settings(0x0000)  # prints register settings in hexadecimal and binary format, consult datasheet

scanner.set_register_settings(0x0000, 0b10001110)  # set LED always on

scanner.set_register_settings(0x0015, 0x63)  # set LED to maximum brightness