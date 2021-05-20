var current_deck = 6;
var markers_users = {};
var markers_aps = {};
var aps_show = true;
var users_show = true;
var crew = false;
var image;
var guid;

// draw the map
var map = L.map("map", {
  crs: L.CRS.Simple,
  minZoom: -2.5,
  zoomSnap: 0.5,
});
// set the bounds
var bounds = [
  [0, 0],
  [800, 5275],
];

var image = L.imageOverlay(
  "/static/img/maps/pax/DECK_" + current_deck + ".png",
  bounds
).addTo(map);
map.fitBounds(bounds);

// map specific conversion
function toPixels(meters) {
  pixels = (meters * 5275) / 350;
  return pixels;
}

// get the guid from cache or create a neww one
function get_guid() {
  if (window.localStorage.guid != null) {
    return window.localStorage.guid;
  } else {
    window.localStorage.guid = window.prompt("ENTER USER ID", "DEVICE NAME");
    return window.localStorage.guid;
  }
}

// deck up
L.easyButton("fa-arrow-up fa-lg", function () {
  if (current_deck != 20) {
    current_deck = current_deck + 1;
  }
  if (current_deck == 13) {
    current_deck = 14;
  }
  update_markers();
  update_map();
}).addTo(map);

// deck down
L.easyButton("fa-arrow-down fa-lg", function () {
  if (current_deck != 0) {
    current_deck = current_deck - 1;
  }
  if (current_deck == 13) {
    current_deck = 12;
  }
  update_markers();
  update_map();
}).addTo(map);

// centre map on self
L.easyButton("fa-crosshairs fa-lg", function () {
  for (const device in markers_users) {
    if (device == guid) {
      current_deck = markers_users[device]["deck"];
      update_markers();
      update_map();
      map.setView(markers_users[device].getLatLng(), 0);
    }
  }
}).addTo(map);

// toggle ap markers flag
L.easyButton("fa-wifi fa-lg", function () {
  aps_show = !aps_show;
  update_markers();
}).addTo(map);

// toggle other users markers flag
L.easyButton("fa-users fa-lg", function () {
  users_show = !users_show;
  update_markers();
}).addTo(map);

// toggle toggle crew view
L.easyButton("fa-user-secret fa-lg", function () {
  crew = !crew;
  update_map();
}).addTo(map);

// update the map level
function update_map() {
  centre = map.getCenter();
  zoom = map.getZoom();
  if (crew) {
    try {
      image.remove();
    } catch (e) {}
    image = L.imageOverlay(
      "/static/img/maps/crew/DECK_" + current_deck + ".jpg",
      bounds
    ).addTo(map);
    map.setView(centre, zoom);
  } else {
    try {
      image.remove();
    } catch (e) {}
    image = L.imageOverlay(
      "/static/img/maps/pax/DECK_" + current_deck + ".png",
      bounds
    ).addTo(map);
    map.setView(centre, zoom);
  }
}

// update makrers fro flags and current level
function update_markers() {
  // aps markers
  if (aps_show) {
    for (const device in markers_aps) {
      if (markers_aps[device]["deck"] != current_deck) {
        markers_aps[device].remove();
      }
      if (markers_aps[device]["deck"] == current_deck) {
        markers_aps[device].addTo(map);
      }
    }
  } else {
    for (const device in markers_aps) {
      markers_aps[device].remove();
    }
  }

  // other users markers
  if (users_show) {
    for (const device in markers_users) {
      if (device != window.localStorage.guid) {
        if (markers_users[device]["deck"] != current_deck) {
          markers_users[device].remove();
        }
        if (markers_users[device]["deck"] == current_deck) {
          markers_users[device].addTo(map);
        }
      }
    }
  } else {
    for (const device in markers_users) {
      if (device != window.localStorage.guid) {
        markers_users[device].remove();
      }
    }
  }

  // self marker
  for (const device in markers_users) {
    if (device == window.localStorage.guid) {
      if (markers_users[device]["deck"] != current_deck) {
        markers_users[device].remove();
      }
      if (markers_users[device]["deck"] == current_deck) {
        markers_users[device].addTo(map);
      }
    }
  }
}

// remove an ap fromt the database
function remove_ap(ap) {
  data = { bssid: ap.innerHTML };
  fetch("/remove", {
    method: "POST", // or 'PUT'
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Success:", data);
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

// retrieve ap location data from server
function fetch_aps() {
  fetch("/aps")
    .then((response) => response.json())
    .then((data) => {
      data.forEach((device) => {
        // add markers
        var sol = L.latLng([
          800 - toPixels(device["y"]),
          toPixels(device["x"]),
        ]);
        var bssid = device["bssid"];

        // ap markers
        markers_aps[device["bssid"]] = L.marker(sol, { icon: greenIcon });
        markers_aps[device["bssid"]]["deck"] = device["z"];

        // add the bssid as a popup
        markers_aps[device["bssid"]].bindPopup(
          '<button type="button" class="btn btn-danger" onclick="remove_ap(this)">' +
            bssid +
            "</button>"
        );
      });
      console.log("Success:", data);
      update_markers();
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

// get the user locations from the database
function fetch_users() {
  fetch("/users")
    .then((response) => response.json())
    .then((data) => {
      // add all the markerts to a list
      data.forEach((device) => {
        var sol = L.latLng([
          800 - toPixels(device["y"]),
          toPixels(device["x"]),
        ]);

        // set self marker to red
        if (device["guid"] == window.localStorage.guid) {
          try {
            markers_users[device["guid"]].setLatLng(sol);
          } catch {
            markers_users[device["guid"]] = L.marker(sol, {
              icon: redIcon,
            });
            markers_users[device["guid"]]["deck"] = device["z"];
          }
        }
        // all other user markers to blue
        else {
          try {
            markers_users[device["guid"]].setLatLng(sol);
          } catch {
            markers_users[device["guid"]] = L.marker(sol, {
              icon: blueIcon,
            });
            markers_users[device["guid"]]["deck"] = device["z"];
          }
        }

        // add the guid as a popup
        markers_users[device["guid"]].bindPopup(
          device["guid"] + " " + device["datetime"]
        );
      });
      console.log("Success:", data);
      update_markers();
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

// get or set the guid
guid = get_guid();

fetch_aps();
update_markers();
setInterval(function () {
  fetch_users();
}, 10000);