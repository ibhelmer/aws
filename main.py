# Import lib
from machine import Pin, I2C
from machine_i2c_lcd import I2cLcd
from machine import SDCard
from machine import RTC
from time import sleep
import network
import os
import _thread
# Define the LCD I2C address and dimensions
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
# Define the TCN75 I2C address
I2C_TMP1_ADDR = 0x48   
I2C_TMP2_ADDR = 0x4C
# Define Wifi symbol
wchar =(0b0000010,0b00001001,0b00000101,0b00010101,0b00010101,0b00000101,0b00001001,0b00000010)
# Define Lock object
lock = _thread.allocate_lock()
# Define global shared ressources
temp1 = 0
temp2 = 0
wifistat = 0
wifistattable = ("Not connected   ", "Connecting...   ","WiFi error      ", "Connected       ")
netconfig = ("","")
def updatescreen():
    global wifistat
    global temp1
    global temp2
    global netconfig
    while True:
        lcd.move_to(0,0)
        if wifistat < 3:
            lcd.putstr(wifistattable[wifistat])
        if wifistat == 3:
            lcd.putstr(str(netconfig[0]))
            lcd.putstr("  "+chr(1))
        lcd.move_to(0,1)
        lock.acquire()
        try:
            lcd.putstr(str(temp1))
            lcd.move_to(8,1)
            lcd.putstr(str(temp2))
        finally:
            lock.release()
        sleep(10)
def connect2wifi():
    global wifistat
    global netconfig
    while True:
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            wifistat = 1
            wlan.active(True)
            wlan.connect('ITLab', 'MaaGodt*7913')
            timeout = 10
            start_time = time.time()
            while not wlan.isconnected():
                if time.time() - start_time > timeout:
                    pass
                sleep(1)
        wifistat = 3
        netconfig = wlan.ipconfig('addr4')
        sleep(30)
def setup_tcn75(adr):
    i2c.writeto_mem(adr, 0x01, b'\x60')
def setup_sdcard():
    # Initialization of SD-Card slot #1
    sd = SDCard(slot=1)  
    # Mounting SD-Card with file system
    vfs = os.VfsFat(sd)
    os.mount(vfs, "/sd")
def read_temp(adr):
    data = i2c.readfrom_mem(adr, 0x00, 2)
    # Convert the data to 12-bits
    temp = ((data[0] * 256) + (data[1] & 0xF0)) / 16
    if temp > 2047 :
        temp -= 4096
    cTemp = temp * 0.0625
    return cTemp
def measurement():
    global temp1
    global temp2
    while True:
        sleep(10)
        lcd.move_to(0,1)
        lock.acquire() #
        try:
            temp1 = read_temp(I2C_TMP1_ADDR)
            temp2 = read_temp(I2C_TMP2_ADDR)
            with open("/sd/tempdiff.csv", "a") as file:
                file.write(str(temp2-temp1)+"\n")
        finally:
            lock.release()
### MAIN starts here ###
# Initialize I2C 
i2c = i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
# Initialize LCD, the two Temp sensors and the RTC clock
# Instantiate classes 
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
rtc=RTC()
# Call setup functions
setup_tcn75(I2C_TMP1_ADDR)
setup_tcn75(I2C_TMP2_ADDR)
setup_sdcard()
# Install user defined char in addr 1 and clear lcd
lcd.custom_char(1,wchar)
lcd.clear()
# Starting threads
_thread.start_new_thread(connect2wifi, ())
_thread.start_new_thread(measurement, ())
_thread.start_new_thread(updatescreen, ())
try:
    while True:
        pass
except KeyboardInterrupt:
    # Turn off the display
    print("Keyboard interrupt")
    lcd.backlight_off()
    lcd.display_off()
    # Unmonte SD-card, when it is not longer in use
    os.umount("/sd")
    print("SD-Card unmontet.")