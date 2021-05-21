# importing libraries needed
from scipy.optimize import minimize
import math
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import mysql.connector
import git
from config import config, gitHubToken


# function to get distance from access point
# ss = signal strength due to access point at a particular point
# rss = reference signal strength at reference distance from access point
# n = signal attenuation factor
# rd = reference distance


def calcDistance(ss, rss, n, rd):
    distance = rd*(10**((rss-ss)/(10*n)))
    return distance


# calculate position form the ap location data
def trilateratePosition(location_data):
    # initial_location: (lat, long)
    # locations: [ (lat1, long1), ... ]
    # distances: [ distance1,     ... ]
    locations = []
    distances = []
    initial_location = (
        float(location_data[0]["x"]), float(location_data[0]["y"]))
    for i in range(len(location_data)):
        locations.append(
            (float(location_data[i]["x"]), float(location_data[i]["y"])))
        distances.append(float(location_data[i]["distance"]))

    def mse(x, locations, distances):
        mse = 0.0
        for location, distance in zip(locations, distances):
            distance_calculated = math.sqrt(
                ((x[0]-location[0])**2)+((x[1]-location[1])**2))
            mse += math.pow(distance_calculated - distance, 2.0)
        return mse / len(distances)

    result = minimize(
        mse,                             # The error function
        initial_location,                # The initial guess
        args=(locations, distances),     # Additional parameters for mse
        method='L-BFGS-B',               # The optimisation algorithm
        options={
            'ftol': 1e-5,                # Tolerance
            'maxiter': 1e+7              # Maximum iterations
        })

    return([result.x[0], result.x[1], location_data[0]["z"]])

# match scanned aps with a known list of locations


def matchBssids(scanned_aps):
    ap_matches = []     # for storing matched aps

    # calculate range from scanned aps
    for i in range(len(scanned_aps)):
        dbm = ((int(scanned_aps[i]["quality"]))/2) - 100
        scanned_aps[i]["dbm"] = dbm

        d = round(calcDistance(dbm, -52, 3.1, 1), 1)
        scanned_aps[i]["distance"] = d

    for ap in scanned_aps:
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        cur.execute("SELECT * FROM ap_locations WHERE bssid=%s", (ap["bssid"],))
        items = cur.fetchall()
        for item in items:
            combined_ap_data = {
                "bssid": item[0], "x": item[1], "y": item[2], "z": item[3], "distance": ap["distance"]}
            ap_matches.append(combined_ap_data)
        con.close()

    if len(ap_matches) > 3:
        ap_matches = ap_matches[0:3]
    for item in ap_matches:
        print(item)
    return ap_matches


app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')


# add an ap to the database
@app.route("/add", methods=['POST'])
def add():
    con = mysql.connector.connect(**config)
    cur = con.cursor()
    cur.execute("REPLACE INTO ap_locations VALUES (%s, %s, %s, %s)",
                (request.json["bssid"], request.json["x"], request.json["y"], request.json["z"],))
    con.commit()
    con.close()
    response = jsonify(
        "Sucessfully added AP: " + request.json["bssid"])
    return response


# remove an ap from the database
@app.route("/remove", methods=['POST'])
def remove():
    con = mysql.connector.connect(**config)
    cur = con.cursor()
    cur.execute(
        "DELETE FROM ap_locations WHERE bssid=%s", (request.json["bssid"],))
    con.commit()
    con.close()
    response = jsonify(
        "Sucessfully removed AP: " + request.json["bssid"])
    return response

# update the location of the device sending the post in the device location db
@app.route("/location", methods=['POST'])
def location():
    id = request.json["guid"]
    matches = matchBssids(request.json["ap_data"])
    if len(matches) > 0:
        coords = trilateratePosition(matches)
        con = mysql.connector.connect(**config)
        cur = con.cursor()
        cur.execute("REPLACE INTO device_locations VALUES (%s, %s, %s, %s, %s)",
                    (id, float(coords[0]), float(coords[1]), float(coords[2]), datetime.now(),))
        con.commit()
        con.close()
        response = jsonify("Sucessfully updated location for guid: " + id)
    else:
        response = jsonify("Location not found")
    return response


# return the locations of connected devices to the frontend
@app.route("/users", methods=['GET'])
def users():
    device_locations = []

    con = mysql.connector.connect(**config)
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM device_locations")
    items = cur.fetchall()

    con.close()

    for item in items:
        device_locations.append(
            dict(zip([c[0] for c in cur.description], item)))

    response = jsonify(device_locations)
    return response

# return the locations of connected devices to the frontend


@app.route("/aps", methods=['GET'])
def aps():
    ap_locations = []

    con = mysql.connector.connect(**config)
    cur = con.cursor()

    # only show devices from the last xxx minutes
    cur.execute(
        "SELECT * FROM ap_locations")
    items = cur.fetchall()

    con.close()

    for item in items:
        ap_locations.append(
            dict(zip([c[0] for c in cur.description], item)))

    response = jsonify(ap_locations)
    return response


@app.route('/update', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('https://' + gitHubToken + ':x-oauth-basic@github.com/josephdouce/wifi-location.git')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(debug=True)
