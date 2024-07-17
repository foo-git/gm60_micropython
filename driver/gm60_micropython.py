# -*- coding: utf-8 -*

import time
from machine import UART


class GM60_Driver:
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
        self._serialport = UART(1, baud, rx=rx, tx=tx)

    def reset_to_factory_defaults(self):
        """
        Resets the barcode scanner back to factory defaults
        """
        data = 0x55

        self.set_register_settings(self.REG_RESET_FACTORY_SETTINGS, data)
        time.sleep(3)  # wait some time to allow the sensor to settle

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

        version_information = {'hardware': hardware_version,
                               'software': software_version,
                               'software_date': software_date}

        return version_information

    def get_register_settings(self, register_address_start, register_read_amount=1):
        """
        Reads one or multiple register values sequentially starting from one register address

        :param register_address_start: Register address value in hexadecimal format, e.g. 0x002A
        :param register_read_amount: Amount of total registers to be read, e.g. 2. Defaults to 1.
        :return: Tuple of hexadecimal and binary content of the register address
        """
        response = self._read_register(register_address_start, register_read_amount)
        data = response[4:4 + register_read_amount]

        data_bin = []
        for item in data:
            data_bin.append(bin(int(item)))

        return data, data_bin

    def read_sensor(self):
        """
        Reads barcode sensor output as long as there is data left to be read.

        :return: String containing the read barcode, or empty list if no data was available.
        """
        response = []
        while self._serialport.any():
            response.append(self._serialport.read())
            time.sleep_ms(5)
        else:
            if response:
                return b''.join(response).decode('utf-8')

    def _read_register(self, register_address_start, register_read_amount=1):
        """
        Reads one or multiple register values sequentially starting from one register address

        :param register_address_start: Register address value in hexadecimal format, e.g. 0x002A
        :param register_read_amount: Amount of total registers to be read, e.g. 2. Defaults to 1.
        :return: List of bytes containing the whole response from the scanner including header and CRC information
        """

        packet = [0x7E, 0x00, 0x07, 0x01, 0x00, 0x00, 0x01]

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

        packet = [0x7E, 0x00, 0x08, 0x01, 0x00, 0x00, 0x00]

        register_address = int(register_address)

        packet[4] = register_address >> 8
        packet[5] = register_address & 0xff
        packet[6] = value

        self._process_packet(packet, return_response=False)

    def _process_packet(self, packet, return_response):
        """
        Takes the byte packet, appends CRC checksum, sends it to the scanner and handles the response

        :param packet: List of bytes to be sent to the scanner
        :param return_response: If set to True, returns the whole response, e.g. when getting register settings.
        :return: List of bytes containing the whole response from the scanner including header and CRC information
        """

        # Calculates and appends CRC prior to sending
        bytes_to_send = list(map(int, packet[2:]))  # discard header
        send_crc = self._check_crc16(bytes_to_send)
        packet.append(int(send_crc[0]))
        packet.append(int(send_crc[1]))
        self._serialport.write(bytes(packet))

        # Wait some time to let the scanner settle before reading response
        while not self._serialport.txdone():
            time.sleep_ms(50)
        time.sleep_ms(200)  # empirical value, lower values might result in no response from scanner when read
        response = self._serialport.read()

        if not response:  # in case of no response, try once again to get a response from the scanner
            time.sleep_ms(500)
            response = self._serialport.read()

        if not response:
            print('ERROR: No response from scanner, maybe a typo in address or byte? Sent "{}" and received "{}"'
                  .format(packet, response))
            raise self.CommError

        response = list(map(hex, response))  # make response more human-friendly readable

        # Extract received CRC
        received_crc = []
        for item in response[-2:]:
            received_crc.append(f"{int(item):#0{4}x}")  # padding for a later str comparison, e.g.0x1 -> 0x01

        # Calculate expected CRC
        sent_bytes = list(map(int, response[2:-2]))
        expected_crc = self._check_crc16(sent_bytes)

        if not received_crc == expected_crc:
            print('ERROR: CRC checksum fail, received "{}" but expected "{}".'
                  .format(received_crc, expected_crc))
            raise self.CommError

        if not response[0] == hex(0x02):
            print('ERROR: No response from scanner, maybe a typo in address or byte? Sent "{}" and received "{}"'
                  .format(packet, response))
            raise self.CommError
        elif return_response:
            return response

    def _check_crc16(self, data: list):
        """
        CRC-16 (CCITT) implemented with a precomputed lookup table
        From https://gist.github.com/oysstu/68072c44c02879a2abf94ef350d1c7c6

        :param data: List of integers/hex containing the payload which the CRC has to cover
        :return: List of hexadecimal strings containing the two CRC bytes, e.g. ['0x01', '0x41']
        """
        data = bytes(data)
        table = [
            0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7, 0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C,
            0xD1AD, 0xE1CE, 0xF1EF, 0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6, 0x9339, 0x8318,
            0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE, 0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4,
            0x5485, 0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D, 0x3653, 0x2672, 0x1611, 0x0630,
            0x76D7, 0x66F6, 0x5695, 0x46B4, 0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC, 0x48C4,
            0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823, 0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969,
            0xA90A, 0xB92B, 0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12, 0xDBFD, 0xCBDC, 0xFBBF,
            0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A, 0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
            0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49, 0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13,
            0x2E32, 0x1E51, 0x0E70, 0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78, 0x9188, 0x81A9,
            0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F, 0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046,
            0x6067, 0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E, 0x02B1, 0x1290, 0x22F3, 0x32D2,
            0x4235, 0x5214, 0x6277, 0x7256, 0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D, 0x34E2,
            0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405, 0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E,
            0xC71D, 0xD73C, 0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634, 0xD94C, 0xC96D, 0xF90E,
            0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB, 0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
            0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A, 0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1,
            0x1AD0, 0x2AB3, 0x3A92, 0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9, 0x7C26, 0x6C07,
            0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1, 0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9,
            0x9FF8, 0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
        ]

        crc = 0x0000
        for byte in data:
            crc = (crc << 8) ^ table[(crc >> 8) ^ byte]
            crc &= 0xFFFF

        # Output formatting
        crc = f'{crc:#0{6}x}'  # CRC needs to be padded to contain 4 elements, e.g. 0x141 -> '0x0141'
        crc = ['0x{}'.format(crc[2:4]), '0x{}'.format(crc[4:6])]  # splits 0x0141 into two bytes ['0x01', '0x41']

        return crc
