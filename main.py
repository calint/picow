import sys
import network
import urequests
import machine
import gc
import ntptime
import utime
import socket
import _thread
from machine import Pin
import secrets

def get_programming_joke() -> str:
    joke_json = urequests.get("https://v2.jokeapi.dev/joke/Programming").json()
    if joke_json["type"] == "single":
        return joke_json["joke"]
    else:
        return joke_json["setup"] + "\n" + joke_json["delivery"]

def get_astronauts_in_space_right_now() -> str:
    astronauts = urequests.get("http://api.open-notify.org/astros.json").json()
    resp = ""
    for i in range(astronauts["number"]):
        resp += astronauts["people"][i]["name"] + "\n"
    return resp.strip()

def get_current_date_time_based_on_ip() -> str:
    time_str = urequests.get("http://worldtimeapi.org/api/ip").json()["datetime"]
    return f"{time_str[0:10]} {time_str[11:19]}"

def get_current_date_time_at_utc_using_ntp() -> str:
    ntptime.settime()
    current_time = utime.localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        current_time[0], current_time[1], current_time[2],
        current_time[3], current_time[4], current_time[5]
    )

def get_temperature_in_celsius() -> float:
    temperature_sensor = machine.ADC(4)
    to_volts = 3.3 / 65535 # 3.3 V / 16 bit resolution
    reading = temperature_sensor.read_u16() * to_volts 
    return round(27 - (reading - 0.706) / 0.001721, 1)

def get_wifi_status() -> str:
    return f"{wlan.ifconfig()[0]}  ({wlan.status('rssi')} dBm)"

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def webserver_root(path: str, query: str, headers: list[str], sock: socket.socket) -> None:
    resp = f"""<!DOCTYPE html><pre>hello from rasberry pico w

path: {path}
query: {query}
headers: {headers}

wifi status:
{get_wifi_status()}

temperature:
{get_temperature_in_celsius()} °C

heap:
allocated: {gc.mem_alloc()} B
free mem: {gc.mem_free()} B

current time at utc:
{get_current_date_time_at_utc_using_ntp()}

current time based on ip:
{get_current_date_time_based_on_ip()}

astronauts in space right now:
{get_astronauts_in_space_right_now()}

random programming joke:
{get_programming_joke()}

"""
    sock.send("HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n")
    sock.send(resp)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def webserver_led(path: str, query: str, headers: list[str], sock: socket.socket) -> None:
    led_on = "checked" if "led=1" in query else ""
    if led_on != "":
        Pin("LED",Pin.OUT).on()
    else:
        Pin("LED",Pin.OUT).off()

    resp = f"""<!DOCTYPE html><title>LED</title>
<form>
    <input name=led type=checkbox value=1 {led_on}> LED
    <input type=submit value=apply>
</form>
"""
    sock.send("HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n")
    sock.send(resp)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def webserver() -> None:
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server_sock = socket.socket()
    # re-use server socket since it is not closed when program stopped and re-run
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(addr)
    server_sock.listen(1)
    print(f"webserver open at {wlan.ifconfig()[0]} on port 80")
    sock = None
    while True:
        try:
            sock, addr = server_sock.accept()
            print(f"client connected from {addr}")
            req = sock.recv(1024).decode("utf-8")
            req_lines = req.splitlines()
            req_first_line = req_lines[0]
            _, uri, _ = req_first_line.split(" ", 2)
            path, query = uri.split("?", 1) if "?" in uri else (uri, "")
            headers = req_lines[1:-1]

            if path == "/":
                webserver_root(path, query, headers, sock)
            elif path == "/led":
                webserver_led(path, query, headers, sock)
            else:
                sock.send("HTTP/1.0 404 Not Found\r\n\r\npath '" + path + "' not found")

            sock.close()
        except Exception as e:
            if sock is not None:
                sock.close()
            print(f"connection closed: {e}")

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

led=Pin("LED",Pin.OUT)

led.on()

# wait for user input before starting
sys.stdin.readline()

gc.collect()
print("allocated:", gc.mem_alloc(), "B")
print("free mem:", gc.mem_free(), "B")

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

print("connected")

led.on()

print("\nwifi status:")
print(get_wifi_status())

print("\ncurrent time from 'worldtimeapi.org' using your IP:")
print(get_current_date_time_based_on_ip())

print("\ncurrent time at UTC from 'ntptime' module:")
print(get_current_date_time_at_utc_using_ntp())

print("\nastronauts in space right now:")
print(get_astronauts_in_space_right_now())

print("\nrandom programming joke:")
print(get_programming_joke())

print("\ntemperature:")
print(f"{get_temperature_in_celsius()} °C")

print("-------------------------------------------------")
# note: rp2040 can only run wifi related code on core 0?
webserver()

