# Information collection

## Barcode reader: GM60
* User manual (PDF)
* dfrobot wiki: https://wiki.dfrobot.com/SKU_SEN0486_Gravity_Ring_2D_QR_Code_Scanner

### Interfaces
* UART (Baud rate: 57600, default 9600)
* Voltage: 3.3V

* Pinout
  * 1 - Black    	   GND 	   Ground
  * 2 - Green    	   RXD 	   TTL Input  (needs to be connected to ESP 32 TX)
  * 3 - Yellow    	   TXD     TTL Output (needs to be connected to ESP 32 RX)
  * 4 - Red    	       VCC 	   3.3V

### Pre-existing drivers or projects
* https://github.com/SmartHome-yourself/barcode-scanner-for-esphome
* https://github.com/DFRobot/DFRobot_GM60
* https://github.com/XDROLLOXD/ESP32_Grocy_Barcode_Scanner
* https://github.com/agronaut/SC16IS752-micropython-library

## Firmware
ESP32_GENERIC-20240602-v1.23.0.bin
