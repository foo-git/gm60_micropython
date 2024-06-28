# GM60 barcode scanner driver for MicroPython and ESP32

## Background
To make the GM60 barcode scanner work with an ESP32 using MicroPython, a driver is needed to handle the input/output to the scanner. The `driver` folder contains this driver, further development resources are located in the `docs` folder.
This driver is used in another project for inventory handling using [Grocy](https://grocy.info/), a great software project.

## Example usage
See `example.py` for all commands.

```
# UART port/naming hint:
# GM60 RX (green cable) needs to be connected to ESP32 TX (e.g. here pin 25)
# GM60 TX (yellow cable) needs to be connected to ESP32 RX (e.g. here pin 26)


# initialize UART connection to GM60 barcode scanner
>>> scanner = GM60_Driver(rx=26, tx=25)


# prints hardware and software version information
>>> scanner.get_version()
{'hardware': 1.0, 'software_date': '2021-09-16', 'software': 1.08}


# resets scanner back to factory settings
>>> scanner.reset_to_factory_defaults()


# prints register settings in hexadecimal and binary format for easier development, consult datasheet for details 
>>> scanner.get_register_settings(0x0000)
Hex: ['0x8e']
Binary: ['0b10001110']
(['0x8e'], ['0b10001110'])


# set LED always on
>>> scanner.set_register_settings(0x0000, 0b10001110)

# set LED to maximum brightness
>>> scanner.set_register_settings(0x0015, 0x63)
```

## References
See `docs/references.md` for other projects using the GM60 barcode scanner. Linked there also is the GM60 datasheet for future reference.