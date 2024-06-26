# tested with:
#   UF2 Bootloader v3.0
#   Model: Raspberry Pi RP2
#   Board-ID: RPI-RP2
#   https://micropython.org/download/RPI_PICO_W/RPI_PICO_W-20231005-v1.21.0.uf2
import sys
import network
import urequests
import machine
import gc
import ntptime
import utime
import socket
from machine import Pin

import wifisecrets

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


def get_random_programming_joke() -> str:
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


def get_date_time_based_on_ip() -> str:
    time_str = urequests.get("http://worldtimeapi.org/api/ip").json()["datetime"]
    return f"{time_str[0:10]} {time_str[11:19]}"


def get_date_time_at_utc_using_ntp() -> str:
    ntptime.settime()
    current_time = utime.localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        current_time[0],
        current_time[1],
        current_time[2],
        current_time[3],
        current_time[4],
        current_time[5],
    )


def get_temperature_in_celsius() -> float:
    temperature_sensor = machine.ADC(4)
    to_volts = 3.3 / 65535  # 3.3 V / 16 bit resolution
    reading = temperature_sensor.read_u16() * to_volts
    return round(27 - (reading - 0.706) / 0.001721, 1)


def get_wifi_status() -> str:
    return f"{wlan.ifconfig()[0]} ({wlan.status('rssi')} dBm)"


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


def webserver_root(
    path: str, query: str, headers: list[str], sock: socket.socket
) -> None:
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
{get_date_time_at_utc_using_ntp()}

current time based on ip:
{get_date_time_based_on_ip()}

astronauts in space right now:
{get_astronauts_in_space_right_now()}

random programming joke:
{get_random_programming_joke()}

"""
    sock.send("HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n")
    sock.send(resp)


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


def webserver_led(
    path: str, query: str, headers: list[str], sock: socket.socket
) -> None:
    led_on = "checked" if "led=1" in query else ""
    led.on() if led_on != "" else led.off()

    resp = f"""<!DOCTYPE html><title>LED</title>
<form>
    <input name=led type=checkbox value=1 {led_on}> LED
    <button type=submit>Apply</button>
</form>
"""
    sock.send("HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n")
    sock.send(resp)


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


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
            req = sock.recv(1024).decode("utf-8")
            req_lines = req.splitlines()
            _, uri, _ = req_lines[0].split(" ", 2)
            path, query = uri.split("?", 1) if "?" in uri else (uri, "")
            headers = req_lines[1:-1]

            print(f"client at '{addr[0]}' requests '{path}' with query '{query}'")

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


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------


def connect_wifi(wlan: network.WLAN) -> None:
    wlan.active(True)

    print(f"\nconnecting to '{wifisecrets.SSID}' using '{wifisecrets.PASSWORD}'")
    wlan.connect(wifisecrets.SSID, wifisecrets.PASSWORD)
    waited = False
    while not wlan.isconnected() and wlan.status() >= 0:
        print(".", end="")
        waited = True
        utime.sleep_ms(500)

    if not wlan.isconnected():
        if wlan.status() == network.STAT_WRONG_PASSWORD:
            raise RuntimeError(
                f"cannot connect to '{wifisecrets.SSID}' "
                "because of authentication problem"
            )

        if wlan.status() == network.STAT_NO_AP_FOUND:
            raise RuntimeError(
                f"cannot connect to '{wifisecrets.SSID}' "
                "because the network is not found"
            )

        if wlan.status() == network.STAT_CONNECT_FAIL:
            raise RuntimeError(
                f"cannot connect to '{wifisecrets.SSID}' status: STAT_CONNECT_FAIL"
            )

        raise RuntimeError(
            f"cannot connect to '{wifisecrets.SSID}' status: {wlan.status()}"
        )

    if waited:
        print()


# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

led = Pin("LED", Pin.OUT)

led.on()

# wait for user input before starting
sys.stdin.readline()

gc.collect()
print("allocated:", gc.mem_alloc(), "B")
print("free mem:", gc.mem_free(), "B")

led.off()

wlan = network.WLAN(network.STA_IF)

connect_wifi(wlan)

led.on()

print("\nwifi status:")
print(get_wifi_status())

print("\ncurrent time from 'worldtimeapi.org' using your IP:")
print(get_date_time_based_on_ip())

print("\ncurrent time at UTC from 'ntptime' module:")
print(get_date_time_at_utc_using_ntp())

print("\nastronauts in space right now:")
print(get_astronauts_in_space_right_now())

print("\nrandom programming joke:")
print(get_random_programming_joke())

print("\ntemperature:")
print(f"{get_temperature_in_celsius()} °C")

# read and write file
try:
    file = open("prefs.txt", "r+")
    boot_count = int(file.read())
except OSError:
    file = open("prefs.txt", "w+")
    boot_count = 1

print("\nboot count:", boot_count)
boot_count += 1
file.seek(0)
file.write(str(boot_count))
file.close()

print("-------------------------------------------------")

# note: rp2040 can only run wifi related code on core 0?
webserver()
