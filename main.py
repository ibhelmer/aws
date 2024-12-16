# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/micropython-i2c-lcd-esp32-esp8266/

from machine import Pin, SoftI2C
from machine_i2c_lcd import I2cLcd
from time import sleep
import network

# Define the LCD I2C address and dimensions
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

# Define the TCN75 I2C address
I2C_TMP1_ADDR = 0x48   
I2C_TMP2_ADDR = 0x4C

def do_connect():
    sta_if = network.WLAN(network.WLAN.IF_STA)
    if not sta_if.isconnected():
        lcd.putstr('connecting...')
        sta_if.active(True)
        sta_if.connect('ITLab', 'MaaGodt*7913')
        while not sta_if.isconnected():
            pass
    lcd.clear() 
    netconfig = sta_if.ipconfig('addr4')
    lcd.putstr(netconfig[0])

def setup_tcn75(adr):
    i2c.writeto_mem(adr, 0x01, b'\x60')
def setup_SD():
    machine.SDCard(slot=1, width=1, cd=None, wp=None, sck=None, miso=None, mosi=None, cs=None, freq=20000000)
    
def read_temp(adr):
    data = i2c.readfrom_mem(adr, 0x00, 2)
    # Convert the data to 12-bits
    temp = ((data[0] * 256) + (data[1] & 0xF0)) / 16
    if temp > 2047 :
        temp -= 4096
    cTemp = temp * 0.0625
    return cTemp

### MAIN starts here ###
# Initialize I2C 
i2c = i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
# Initialize LCD and the two Temp sensors
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
setup_tcn75(I2C_TMP1_ADDR)
setup_tcn75(I2C_TMP2_ADDR)

lcd.clear()
do_connect()
try:
    while True:
        sleep(2)
        lcd.move_to(0,1)
        lcd.putstr(str(read_temp(I2C_TMP1_ADDR)))
        lcd.move_to(8,1)
        lcd.putstr(str(read_temp(I2C_TMP2_ADDR)))
        
except KeyboardInterrupt:
    # Turn off the display
    print("Keyboard interrupt")
    lcd.backlight_off()
    lcd.display_off()