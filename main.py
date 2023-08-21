import sys
import network
import secrets
import time
import urequests
import machine
import gc
import ntptime
import utime
from machine import Pin

led=Pin("LED",Pin.OUT)

led.on()

# wait for user input before starting
sys.stdin.readline()

gc.collect()
print("free mem:", gc.mem_free())
led.off()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("\nconnecting to:", secrets.SSID)
wlan.connect(secrets.SSID, secrets.PASSWORD)
while not wlan.isconnected():
    print("  waiting for connection")
    time.sleep(2)

led.on()

print("\nIP:", wlan.ifconfig()[0])
print("signal strength (RSSI):", wlan.status('rssi'), "dBm")


print("\ncurrent time from 'worldtimeapi.org' using your IP:")
time_string = urequests.get("http://worldtimeapi.org/api/ip").json()["datetime"]
# 2023-08-21T14:34:31.178704+02:00
date, time_ = time_string.split("T")
year, month, day = date.split("-")
hour, minute, second, _ = time_.split(":")
second = second.split(".")[0]  # remove the fractional part of seconds
formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
    int(year), int(month), int(day), int(hour), int(minute), int(second)
)
print(formatted_time)


print("\ncurrent time at UTC from 'ntptime' module:")
ntptime.settime()
current_time = utime.localtime()
formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
    current_time[0], current_time[1], current_time[2],
    current_time[3], current_time[4], current_time[5]
)
print(formatted_time)


print("\nastronauts in space right now:")
astronauts = urequests.get("http://api.open-notify.org/astros.json").json()
for i in range(astronauts['number']):
    print(astronauts['people'][i]['name'])


print("\ntemperature:")
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / 65535 # 3.3 V / 16 bit resolution

while True:
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature = 27 - (reading - 0.706) / 0.001721
    print(temperature)
    time.sleep(2)