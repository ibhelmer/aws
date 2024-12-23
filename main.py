from machine import Pin, SoftI2C
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


wchar =(0b0000010,0b00001001,0b00000101,0b00010101,0b00010101,0b00000101,0b00001001,0b00000010)
lock = _thread.allocate_lock()
# Define shared ressources
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
        lcd.putstr(str(temp1))
        lcd.move_to(8,1)
        lcd.putstr(str(temp2))   
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
            start_tiem = time.time()
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
    # Initialisering af SD-kortet slot #1
    sd = SDCard(slot=1)  
    # Montering af SD-kort som et filsystem
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
        temp1 = read_temp(I2C_TMP1_ADDR)
        temp2 = read_temp(I2C_TMP2_ADDR)
        with open("/sd/tempdiff.csv", "a") as file:
            file.write(str(temp2-temp1)+"\n")    
### MAIN starts here ###
# Initialize I2C 
i2c = i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
# Initialize LCD and the two Temp sensors
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
lcd.custom_char(1,wchar)
rtc=RTC()

setup_tcn75(I2C_TMP1_ADDR)
setup_tcn75(I2C_TMP2_ADDR)
setup_sdcard()

lcd.clear()
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
    # Afmonter SD-kortet, når det ikke længere skal bruges
    os.umount("/sd")
    print("SD-kort unmontet.")