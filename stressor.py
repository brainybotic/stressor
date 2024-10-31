import requests
import time
import threading
import random
import keyboard
import sys
import os
from geojson import Point
import json
import uuid

# Configurations using 0-10 scale instead of percentages
config = {
    "target_url_distribution": {
        'http://192.168.40.2': 5,           # Scale 0-10
        'http://192.168.40.3': 3,
        'http://192.168.40.2:8093': 1,
        'http://192.168.40.3:9380': 1
    },
    "method_distribution": {
        "GET": 6,      # Scale 0-10
        "POST": 2,
        "DELETE": 1,
        "PATCH": 1
    },
    "error_path_distribution": {
        '/': 4,
        '/nonexistentpage': 2,
        '/forbidden': 1,
        '/internalerror': 1,
        '/unauthorized': 1,
        '/invalidquery?param=': 1
    },
    "user_agent_distribution": {
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36': 3,
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0.2 Safari/605.1.15': 3,
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0': 2,
        'Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36': 1,
        'Mozilla/5.0 (Linux; Android 11; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36': 1
    },
    "requests_per_second": 1  # Starting requests per second
}

# Helper functions to set up distributions
def build_weighted_choice_list(distribution_dict):
    """Converts a distribution dictionary with scale 0-10 into a weighted list for random.choice."""
    return [key for key, weight in distribution_dict.items() for _ in range(weight)]

# Initialize weighted choices based on the configuration
target_choices = build_weighted_choice_list(config["target_url_distribution"])
method_choices = build_weighted_choice_list(config["method_distribution"])
error_path_choices = build_weighted_choice_list(config["error_path_distribution"])
user_agent_choices = build_weighted_choice_list(config["user_agent_distribution"])

# Global variables
requests_per_second = config["requests_per_second"]
stop_threads = False

# Function to generate a random JSON payload for POST and PATCH requests
def generate_random_payload():
    return {
        "name": random.choice(["Alice", "Bob", "Charlie", "David"]),
        "value": random.randint(1, 100),
        "status": random.choice(["active", "inactive", "pending"])
    }

# Define IPs and associated coordinates
ip_coordinates = {
    "10.0.0.90": {"latitude": 38.7169, "longitude": -9.1399},  # Coordinates for Lisbon
    "10.0.0.91": {"latitude": 34.0522, "longitude": -118.2437},   # Los Angeles
    "10.0.0.92": {"latitude": 40.7128, "longitude": -74.0060},    # New York
    "10.0.0.93": {"latitude": 51.5074, "longitude": -0.1278},     # London
    "10.0.0.94": {"latitude": 35.6895, "longitude": 139.6917},    # Tokyo
    "10.0.0.95": {"latitude": 48.8566, "longitude": 2.3522},      # Paris
    "10.0.0.96": {"latitude": -33.8688, "longitude": 151.2093},   # Sydney
    "10.0.0.97": {"latitude": 55.7558, "longitude": 37.6173},     # Moscow
    "10.0.0.98": {"latitude": -34.6037, "longitude": -58.3816},   # Buenos Aires
    "10.0.0.99": {"latitude": 28.6139, "longitude": 77.2090}      # Delhi
}


'''
geoDataFile = "c:/code/geomap/geodata.geojson"


def createGeoDataFile(fake_ip, coordinates):
    # create a new python dict to contain our geojson data, using geojson format
    geojson = {'type': 'FeatureCollection', 'metadata': {'count': 10}, 'features': []}
    
    # loop through each row in the dataframe 
#    for key, value in dictionary.items():
    # create a feature template to fill in
    feature = {'type': 'Feature', 
                'properties': {},
                'geometry': {'type':'Point',
                            'coordinates':()},
                'id': f'{uuid.uuid4()}'}
    
    # fill in the coordinates 
    # feature['geometry']['coordinates'] = [value]
    feature['geometry']['coordinates'] = (coordinates['longitude'], coordinates['latitude'])

    
    # create properies with region id
    feature['properties']['ip'] = fake_ip
    # add this feature (convert dataframe row) to the list of features inside our dict
    geojson['features'].append(feature)


    with open(geoDataFile, 'w') as f:
        f.write(json.dumps(geojson))    
    
    return geojson

def appendGeoDataFile(fake_ip, coordinates):

    # Load existing data
    with open(geoDataFile) as f:
        geojson = json.load(f)


    # loop through each row in the dataframe 
#    for key, value in dictionary.items():
    # create a feature template to fill in
    feature = {'type': 'Feature', 
                'properties': {},
                'geometry': {'type':'Point',
                            'coordinates':()},
                'id': f'{uuid.uuid4()}'}
        
    # fill in the coordinates 
    # feature['geometry']['coordinates'] = [value]
    feature['geometry']['coordinates'] = (coordinates['longitude'], coordinates['latitude'])
    
    # create properies with region id
    feature['properties']['ip'] = fake_ip
    # add this feature (convert dataframe row) to the list of features inside our dict
    geojson['features'].append(feature)

    # Limit to the last five features
    if len(geojson['features']) > 5:
        geojson['features'] = geojson['features'][-5:]

    with open(geoDataFile, 'w') as f:
        f.write(json.dumps(geojson))    
    
    return geojson


def updateGeoDataFile(fake_ip, coordinates):
    if os.path.exists(geoDataFile):
       appendGeoDataFile(fake_ip, coordinates)
    else:
       createGeoDataFile(fake_ip, coordinates)
'''



# Global variables for caching
geoDataFile = "c:/code/geomap/geodata.geojson"
geojson_cache = {'type': 'FeatureCollection', 'metadata': {'count': 10}, 'features': []}
cache_size = 5  # Limit cache size

def updateGeoDataFile(fake_ip, coordinates):
    global geojson_cache
    '''
    # Check if IP is already in cache, replace it, or add it as a new entry
    for feature in geojson_cache['features']:
        if feature['properties']['ip'] == fake_ip:
            feature['geometry']['coordinates'] = [coordinates['longitude'], coordinates['latitude']]
            break
    else:
    '''
    # Add new feature to cache
    geojson_cache['features'].append({
        'type': 'Feature',
        'properties': {'ip': fake_ip},
        'geometry': {'type': 'Point', 'coordinates': [coordinates['longitude'], coordinates['latitude']]},
        'id': str(uuid.uuid4())
    })

    # Trim cache to limit size and write to file
    if len(geojson_cache['features']) > cache_size:
        geojson_cache['features'] = geojson_cache['features'][-cache_size:]
        with open(geoDataFile, 'w') as f:
            json.dump(geojson_cache, f, indent=2)
        geojson_cache = {'type': 'FeatureCollection', 'metadata': {'count': 10}, 'features': []}





# Function to send spoofed requests with geo-coordinates
def send_spoofed_request():
    global stop_threads
    while not stop_threads:
        for _ in range(requests_per_second):
            if stop_threads:
                break

            target_url = random.choice(target_choices)
            method = random.choice(method_choices)
            error_path = random.choice(error_path_choices)
            user_agent = random.choice(user_agent_choices)
            fake_ip = f"10.0.0.{random.randint(90, 99)}"
            url = target_url + error_path

            # Add geographic coordinates from IP mapping
            coordinates = ip_coordinates.get(fake_ip, {"latitude": 0.0, "longitude": 0.0})

            print(coordinates['latitude'], coordinates['longitude'])
            updateGeoDataFile(fake_ip, coordinates)
            #with open(geoDataFile, 'a+') as f:
            #    f.write(str(Point((coordinates['latitude'], coordinates['longitude']))))

            headers = {
                'X-Forwarded-For': fake_ip,
                'User-Agent': user_agent,
                'X-Latitude': str(coordinates["latitude"]),
                'X-Longitude': str(coordinates["longitude"])
            }

            try:
                if method == "GET":
                    response = requests.get(url, headers=headers)
                elif method == "POST":
                    payload = generate_random_payload()
                    payload.update(coordinates)  # Add coordinates to payload if POST or PATCH
                    response = requests.post(url, headers=headers, json=payload)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers)
                elif method == "PATCH":
                    payload = generate_random_payload()
                    payload.update(coordinates)
                    response = requests.patch(url, headers=headers, json=payload)

                print(f"Sent {method} request to {url} from {fake_ip} with coordinates {coordinates} - Status Code: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"Error sending {method} request to {url} from {fake_ip}: {e}")

            time.sleep(1 / max(requests_per_second, 1))  # Control the interval between requests

# Thread to monitor keyboard input and adjust request rate
def monitor_keyboard():
    global requests_per_second, stop_threads
    while not stop_threads:
        if keyboard.is_pressed('+'):
            requests_per_second += 1
            print(f"Requests per second increased to: {requests_per_second}")
            time.sleep(0.2)
        elif keyboard.is_pressed('-') and requests_per_second > 0:
            requests_per_second -= 1
            print(f"Requests per second decreased to: {requests_per_second}")
            time.sleep(0.2)

# Start the threads
try:
    print("[*] Starting botnet attack. Use '+' to increase and '-' to decrease the requests per second.")
    attack_thread = threading.Thread(target=send_spoofed_request, daemon=True)
    keyboard_thread = threading.Thread(target=monitor_keyboard, daemon=True)

    # Start both threads
    attack_thread.start()
    keyboard_thread.start()

    # Keep the main thread alive while sub-threads run
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[*] Attack interrupted by user. Stopping threads...")
    stop_threads = True  # Signal threads to stop
    attack_thread.join()
    keyboard_thread.join()
    print("[*] Attack stopped.")
    sys.exit(0)
