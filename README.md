# GM60 barcode scanner driver for MicroPython and ESP32

## Background
To make the GM60 barcode scanner work with an ESP32 using MicroPython, a driver is needed to handle the input/output to the scanner. The `driver` folder contains this driver, further development resources are located in the `docs` folder.
This driver is used in another project for inventory handling using [Grocy](https://grocy.info/), a great software project.

## Features
* Comfortable I/O commands make working with the datasheet easier
* CRC support for incoming and outgoing packets

## Example usage
See `example.py` for runnable commands.

```
# Load driver
>>> from gm60_micropython import GM60_Driver


# Initialize UART connection to GM60 barcode scanner
    # UART port/naming hint:
    # GM60 RX (green cable) needs to be connected to ESP32 TX (e.g. here pin 25)
    # GM60 TX (yellow cable) needs to be connected to ESP32 RX (e.g. here pin 26)
>>> scanner = GM60_Driver(rx=26, tx=25)


# Prints hardware and software version information
>>> scanner.get_version()
{'hardware': 1.0, 'software_date': '2021-09-16', 'software': 1.08}


# Resets scanner back to factory settings
>>> scanner.reset_to_factory_defaults()


# Prints register settings in hexadecimal and binary format for easier development
>>> scanner.get_register_settings(0x0000)
(['0x8e'], ['0b10001110'])


# Set LED always on
>>> scanner.set_register_settings(0x0000, 0b10001110)

# Set LED to maximum brightness
>>> scanner.set_register_settings(0x0015, 0x63)

# Read barcode from sensor
>>> scanner.read_barcode()
'4066447241358'
```

![Circuit diagram for GM60 and ESP32](https://github.com/foo-git/gm60_micropython/blob/main/docs/circuit.png?raw=true)

![Photo of GM60 and ESP32 proof-of-concept build](https://github.com/foo-git/gm60_micropython/blob/main/docs/poc.jpg?raw=true)

## References
See `docs/references.md` for other projects using the GM60 barcode scanner. Linked there also is the GM60 datasheet for future reference.