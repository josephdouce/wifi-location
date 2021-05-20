import requests
import platform
from access_points import get_scanner
import time
from winwifi import WinWiFi

SERVER = "https://josephdouce.pythonanywhere.com/location"

while True:
    try:
        scan = WinWiFi.scan()
        wifi_scanner = get_scanner()
        aps = wifi_scanner.get_access_points()
        aps = sorted(aps, key=lambda k: k['quality'], reverse=True)
        filtered_aps = list(filter(lambda ap: ap["ssid"] == "ION_Lan", aps))
        for ap in filtered_aps:
            print(ap)

        ap_data = filtered_aps
        guid = platform.node()

        post_data = {"ap_data":ap_data, "guid":guid}
        response = requests.post(SERVER, json = post_data)

        print(response)
        time.sleep(15)
    except:
        print("Unable to contact server!")
        time.sleep(15)