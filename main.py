import sys
import network
import secrets
import urequests
import machine
import gc
import ntptime
import utime
import socket
import _thread
from machine import Pin

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def webserver():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    # re-use server socket since it is not closed when program stopped and re-run
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print(f"listening on {addr}")
    while True:
        try:
            cl, addr = s.accept()
            print(f"client connected from {addr}")
            request = cl.recv(1024)
            response = f"<pre>hello from rasberry pico w {utime.localtime()}\n{request}"
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.send(response)
            cl.close()
        except OSError as e:
            if cl is not None:
                cl.close()
            print('connection closed')

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

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
while not wlan.isconnected() and wlan.status() >= 0:
    print("  waiting for connection")
    utime.sleep(2)

if not wlan.isconnected():
    if wlan.status() == network.STAT_WRONG_PASSWORD:
        raise RuntimeError(f"cannot connect to '{secrets.SSID}' because of authentication problem")

    if wlan.status() == network.STAT_NO_AP_FOUND:
        raise RuntimeError(f"cannot connect to '{secrets.SSID}' because the network is not found")

    if wlan.status() == network.STAT_CONNECT_FAIL:
        raise RuntimeError(f"cannot connect to '{secrets.SSID}' status: STAT_CONNECT_FAIL")

    raise RuntimeError(f"cannot connect to '{secrets.SSID}' status: {wlan.status()}")

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
temperature_sensor = machine.ADC(4)
to_volts = 3.3 / 65535 # 3.3 V / 16 bit resolution
reading = temperature_sensor.read_u16() * to_volts 
celsius_degrees = 27 - (reading - 0.706) / 0.001721
print(f"{celsius_degrees} °C\n")

# running on second core replies only once. bug?
# tried micropython:
#    rp2-pico-w-20230426-v1.20.0.uf2
#    micropython-firmware-pico-w-130623.uf2
#_thread.start_new_thread(webserver, ())
#while True:
#    utime.sleep(5)
webserver()

#while True:
#    reading = temperature_sensor.read_u16() * to_volts 
#    celsius_degrees = 27 - (reading - 0.706) / 0.001721
#    print(f"{celsius_degrees} °C")
#    utime.sleep(2)