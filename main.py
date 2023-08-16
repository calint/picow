from machine import Pin
from utime import sleep

pin = Pin("LED", Pin.OUT)

print(pin)
while True:
    pin.toggle()
    sleep(1)