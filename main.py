import sys
import network
import secrets
import time
import urequests
import machine
import gc
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

print("connecting to:", secrets.SSID)
wlan.connect(secrets.SSID, secrets.PASSWORD)
while not wlan.isconnected():
    print("  waiting for connection")
    time.sleep(2)

led.on()

print("IP:", wlan.ifconfig()[0])
print("Signal Strength (RSSI):", wlan.status('rssi'), "dBm")

print("\nAstronauts in space right now:")
astronauts = urequests.get("http://api.open-notify.org/astros.json").json()
for i in range(astronauts['number']):
    print(astronauts['people'][i]['name'])

print("\nTemperature:")
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / 65535

while True:
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature = 27 - (reading - 0.706) / 0.001721
    print(temperature)
    time.sleep(2)