import network
import secrets
import time
import urequests
from machine import Pin

led = Pin("LED", Pin.OUT)
led.off()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.SSID, secrets.PASSWORD)

if wlan.isconnected():
    led.on()

astronauts = urequests.get("http://api.open-notify.org/astros.json").json()

for i in range(astronauts['number']):
    print(astronauts['people'][i]['name'])