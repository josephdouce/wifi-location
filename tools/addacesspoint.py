# importing libraries needed
import cv2
import requests
from tkinter import messagebox
from access_points import get_scanner
from winwifi import WinWiFi

deck = 3
SERVER = "https://josephdouce.pythonanywhere.com/add"

# function to display the coordinates of
# of the points clicked on the image
def click_event(event, x, y, flags, params):

    # checking for left mouse clicks
    if event == cv2.EVENT_LBUTTONDOWN:

        # displaying the coordinates
        # on the Shell
        scan = WinWiFi.scan()
        wifi_scanner = get_scanner()
        all_aps = wifi_scanner.get_access_points()
        filtered_aps = list(
            filter(lambda ap: ap["ssid"] == "ION_Lan", all_aps))
        filtered_aps = list(
            filter(lambda ap: ap["radio"] == "802.11ac", filtered_aps))
        sorted_aps = sorted(
            filtered_aps, key=lambda k: k['quality'], reverse=True)
        for i in range(3):
            print(sorted_aps[i])
        best_ap = sorted_aps[0]
        meters_x = round(x*350/5275, 1)
        meters_y = round(y*350/5275, 1)
        z = deck

        post_data = {"bssid":best_ap["bssid"], "x":meters_x, "y":meters_y, "z":z}
        response = requests.post(SERVER, json = post_data)

        print(response)

        # add ap to the ap_locations database table
        messagebox.showinfo(title="New AP", message="Added: " + best_ap["bssid"] + "\nx: " + str(
            meters_x) + "\ny: " + str(meters_y) + "\ndeck: " + str(z))

    # checking for right mouse clicks
    if event == cv2.EVENT_RBUTTONDOWN:

        print("right click")


# driver function
if __name__ == "__main__":

    # reading the image
    img = cv2.imread('../static/img/maps/crew/DECK_'+str(deck)+'.jpg', 1)

    # displaying the image
    cv2.namedWindow('Add AP', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Add AP', int(5275/3), int(800/3))
    cv2.imshow('Add AP', img)

    # setting mouse hadler for the image
    # and calling the click_event() function
    cv2.setMouseCallback('Add AP', click_event)

    # wait for a key to be pressed to exit
    cv2.waitKey(0)

    # close the window
    cv2.destroyAllWindows()
