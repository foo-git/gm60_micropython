# -*- coding: utf-8 -*

import time
from machine import UART


class GM60_Driver():
    REG_RESET_FACTORY_SETTINGS = 0X00D9  # register for restoring factory settings

    class CommError(Exception):  # custom exception for handling errors related to communication with the scanner
        pass

    def __init__(self, rx, tx, baud=9600):
        """
        Initializes the UART connection to the barcode scanner

        :param rx: Pin number of ESP32 UART RX pin in integer format, e.g. 25
        :param tx: Pin number of ESP32 UART TX pin in integer format, e.g. 26
        :param baud: Baudrate of the UART connection in integer format. Defaults to 9600.
        """
        self.ser = UART(1, baud, rx=rx, tx=tx)

    def reset_to_factory_defaults(self):
        """
        Resets the barcode scanner back to factory defaults

        :return: Dict containing hardware revision, software version and date
        """
        data = 0x55

        self.set_register_settings(self.REG_RESET_FACTORY_SETTINGS, data)
        time.sleep(1)  # wait some time to allow the sensor to settle

    def get_version(self):
        """
        Gets hardware and software information of the barcode scanner

        :return: Dict containing hardware revision, software version and date
        """
        response = self._read_register(0x00E1, 5)
        hardware_version = int(response[4]) / 100
        software_version = int(response[5]) / 100

        # date in format YYYY-MM-DD
        software_date = '{:04d}-{:02d}-{:02d}'.format(int(response[6]) + 2000, int(response[7]), int(response[8]))

        version_information = {'hardware': hardware_version, 'software': software_version, 'software_date': software_date}

        return version_information

    def get_register_settings(self, register_address_start, register_read_amount=1):
        """
        Reads one or multiple register values sequentially starting from one register address

        :param register_address_start: Register address value in hexadecimal format, e.g. 0x002A
        :param register_read_amount: Amount of total registers to be read, e.g. 2. Defaults to 1.
        :return: Tuple of hexadecimal and binary content of the register address
        """
        response = self._read_register(register_address_start, register_read_amount)
        data = response[4:4+register_read_amount]
        print('Hex: {}'.format(data))

        data = response[4:4 + register_read_amount]
        data_bin = []
        for item in data:
            data_bin.append(bin(int(item)))
        print('Binary: {}'.format(data_bin))

        return data, data_bin

    def read_sensor(self):
        response = self.ser.readline()

        return response

    def _read_register(self, register_address_start, register_read_amount=1):
        """
        Reads one or multiple register values sequentially starting from one register address

        :param register_address_start: Register address value in hexadecimal format, e.g. 0x002A
        :param register_read_amount: Amount of total registers to be read, e.g. 2. Defaults to 1.
        :return: List of bytes containing the whole response from the scanner including header and CRC information
        """

        packet = [0x7E, 0x00, 0x07, 0x01, 0x00, 0x00, 0x01, 0xAB, 0xCD]

        register_address_start = int(register_address_start)

        packet[4] = register_address_start >> 8
        packet[5] = register_address_start & 0xff
        packet[6] = register_read_amount

        return self._process_packet(packet, return_response=True)

    def set_register_settings(self, register_address, value):
        """
        Sets one register to a certain value

        :param register_address: Register address value in hexadecimal format, e.g. 0x001F
        :param value: Value to be set in register in hexadecimal or binary format, e.g. 0b00100001 or 0x39
        """

        packet = [0x7E, 0x00, 0x08, 0x01, 0x00, 0x00, 0x00, 0xAB, 0xCD]

        register_address = int(register_address)

        packet[4] = register_address >> 8
        packet[5] = register_address & 0xff
        packet[6] = value

        self._process_packet(packet)

    def _process_packet(self, packet, return_response=False):
        """
        Takes the byte packets, sends it to the scanner and handles the response

        :param packet: List of bytes to be sent to the scanner
        :param return_response: If set to True, returns the whole response, e.g. when getting register settings. Defaults to False.
        :return: List of bytes containing the whole response from the scanner including header and CRC information
        """
        self.ser.write(bytes(packet))
        while not self.ser.txdone():
            time.sleep_ms(50)

        time.sleep_ms(200)  # empirical value, lower values might result in no response from scanner when read
        response = self.ser.read()
        if not response:  # in case of no response, try once again to get a response from the scanner
            time.sleep_ms(500)
            response = self.ser.read()

        if not response:
            print('ERROR: No response from scanner, maybe a typo in address or byte? Sent "{}" and received "{}"'.format(packet, response))
            raise self.CommError
        response = list(map(hex, response))

        # CRC-16 CCITT check could be processed here

        if not response[0] == hex(0x02):
            print('ERROR: No response from scanner, maybe a typo in address or byte? Sent "{}" and received "{}"'.format(packet, response))
            raise self.CommError
        elif return_response:
            return response
