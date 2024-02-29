# 2024 STM32 Wireless Innovation Design Contest / Heart Clock in <100 lines of Micropython
# https://www.elektormagazine.com/news/stm32-contest-submission-deadline-extended-to-march-1-2024
# Ctrl + C to STOP ! & Ctrl + D to Reboot and execute main.py
import machine					# Pin, ADC, RTC, I2C ... are defined
import Bluetooth_BLE 			# Bluetooh BLE for STM32WB
import Display 					# OLED Display

BLE_Name = "2024_STM32W_Elektor_Ch" # Connect with Bluefruit LE Connect Android (V2) App
UUID_UART = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
UUID_TX = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
UUID_RX = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
uart = Bleuart(BLE_Name, UUID_UART, UUID_TX, UUID_RX)
uart.close()

machine.Pin("A3", machine.Pin.OUT).low() 	# GND Display Power Supply
machine.Pin("A2", machine.Pin.OUT).high()	# VCC Display Power Supply
i2c = machine.SoftI2C(scl=machine.Pin("A1"), sda=machine.Pin("A0"))
oled = Display.SSD1306_I2C(128, 64, i2c)	# Display is 128x64 pixels

adc = ADC("A7") 

rtc = machine.RTC()
rtc.datetime((2023, 4, 16, 0, 11, 20, 0, 0))

HEART = [
[ 0, 0, 0, 0, 0, 0, 0, 0, 0],
[ 0, 1, 1, 0, 0, 0, 1, 1, 0],
[ 1, 1, 1, 1, 0, 1, 1, 1, 1],
[ 1, 1, 1, 1, 1, 1, 1, 1, 1],
[ 1, 1, 1, 1, 1, 1, 1, 1, 1],
[ 0, 1, 1, 1, 1, 1, 1, 1, 0],
[ 0, 0, 1, 1, 1, 1, 1, 0, 0],
[ 0, 0, 0, 1, 1, 1, 0, 0, 0],
[ 0, 0, 0, 0, 1, 0, 0, 0, 0],]

MAX_HISTORY = 250
TOTAL_BEATS = 30
last_y = 0

def calculate_bpm(beats):
    if beats:
        beat_time = beats[-1] - beats[0]
        if beat_time:
            return (len(beats) / (beat_time)) * 60

def refresh(bpm, beat, v, minima, maxima, FrameBuffer):
    global last_y
    
    oled.vline(0, 0, 32, 0)
    FrameBuffer.scroll(-1,0)
    if maxima-minima > 0:
        y = 48 - int(32 * (v-minima) / (maxima-minima))
        FrameBuffer.line(125, last_y, 125, y, 1)
        last_y = y    
    oled.blit(FrameBuffer, 0, 0)
    oled.fill_rect(0,0,120,10,0)     # Clear top and down text area
    oled.fill_rect(0,10,70,10,0) 
    if bpm:
        oled.text("%d bpm" % bpm, 15, 10)
    if beat:							    # Draw heart if beating.
        for y, row in enumerate(HEART):
            for x, c in enumerate(row):
                oled.pixel(x + 2, y + 10, c)    
    Y,M,d,wd,h,m,s,ms = rtc.datetime() # Format YYYY MM DD DayOfWeeek HH MM SS MS
    oled.text(f"{d:02}/{M:02}/{Y:04}", 0, 55)
    oled.text(f"{h:02}:{m:02}:{s:02}", 65, 0)
    oled.show()

def detect():
    history = []
    beats = []
    beat = False
    bpm = None
    oled.fill(0)
    FrameBuffer = framebuf.FrameBuffer(bytearray(128 * 8), 128, 64, framebuf.MONO_HLSB)
    while True:
        v = adc.read()
        history.append(v)
        history = history[-MAX_HISTORY:]	# Get the tail, up to MAX_HISTORY length
        minima, maxima = min(history), max(history)
        threshold_on = (minima + maxima * 3) // 4   # 3/4
        threshold_off = (minima + maxima) // 2      # 1/2
        if v > threshold_on and beat == False:
            beat = True
            beats.append(time.time())
            beats = beats[-TOTAL_BEATS:] 	# Truncate beats queue to max
            bpm = calculate_bpm(beats)
            print(bpm)
            uart.write(str(bpm) + '\n')
        if v < threshold_off and beat == True:
            beat = False
        refresh(bpm, beat, v, minima, maxima, FrameBuffer)
        
detect()
