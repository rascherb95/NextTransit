from google.transit import gtfs_realtime_pb2
from datetime import datetime, timedelta
import requests
import serial
import time

# Constants
SUBWAY_FEED_URL = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw'
API_KEY = "YOUR_API_KEY_HERE"
BUS_STOP_ID = "MTA_401756"  # Your MTA Bus stop here
SUBWAY_STOP_ID = "Q03S"  # Your subway stop here
LINE_REFS = ["MTA NYCT_M15", "MTA NYCT_M15+"]  # The buses you want to track
SERIAL_PORT = 'COM3'  # The port for your Arduino
BAUD_RATE = 9600
REFRESH_INTERVAL = 10  # in seconds

# Function to fetch and parse GTFS real-time data for subway
def fetch_gtfs_feed(url):
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        response = requests.get(url)
        response.raise_for_status()
        feed.ParseFromString(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching subway feed: {e}")
    return feed

# Function to fetch bus data from MTA API
def get_stop_monitoring(api_key, stop_id, line_ref=None):
    base_url = "http://bustime.mta.info/api/siri/stop-monitoring.json"
    params = {
        "key": api_key,
        "MonitoringRef": stop_id
    }
    if line_ref:
        params["LineRef"] = line_ref

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bus data: {e}")
        return None

# Bus class to encapsulate bus information
class Bus:
    def __init__(self, est_arrival, bus_type):
        self.est_arrival = est_arrival
        self.bus_type = bus_type

    def get_time_difference(self):
        future_time_str = self.est_arrival[11:19]  # ISO8601 format spliced to obtain time
        now = datetime.now()

        future_time = datetime.strptime(future_time_str, "%H:%M:%S").time()
        future_datetime = datetime.combine(now.date(), future_time)

        if future_datetime < now:
            future_datetime += timedelta(days=1)

        time_diff = future_datetime - now
        return round(time_diff.total_seconds() / 60), round(time_diff.total_seconds() % 60)

# Function to send data to Arduino
def send_to_arduino(data):
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            time.sleep(2)  # Wait for the connection to establish
            ser.write(data.encode())
    except serial.SerialException as e:
        print(f"Error: {e}")

# Function to fetch and process bus data
def fetch_and_process_bus_data(api_key, stop_id, line_refs):
    all_buses = []
    for line_ref in line_refs:
        data = get_stop_monitoring(api_key, stop_id, line_ref)
        if data:
            bus_data = data['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']
            for visit in bus_data:
                est_arrival = visit['MonitoredVehicleJourney']['MonitoredCall'].get('ExpectedArrivalTime', None)
                if est_arrival:
                    bus_type = visit['MonitoredVehicleJourney']['PublishedLineName']
                    bus = Bus(est_arrival, bus_type)
                    all_buses.append(bus)
    return all_buses

# Function to process and format bus data
def process_bus_data(buses, limit=2):
    ranked_buses = sorted(buses, key=lambda bus: bus.get_time_difference())[:limit]
    bus_output = []
    for bus in ranked_buses:
        minutes, seconds = bus.get_time_difference()
        if minutes >= 0 and seconds >= 0:
            bus_type_short = (bus.bus_type[:8] + '..') if len(bus.bus_type) > 8 else bus.bus_type
            bus_output.append(f"{bus_type_short:<8} {minutes:2}m {seconds:2}s")
    return bus_output

# Function to process and format subway data
def process_subway_data(feed, stop_id=SUBWAY_STOP_ID, limit=2):
    subway_trains = []
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            for stop_time_update in entity.trip_update.stop_time_update:
                if stop_time_update.stop_id == stop_id:
                    arrival_timestamp = stop_time_update.arrival.time
                    arrival_datetime = datetime.fromtimestamp(arrival_timestamp, tz=None)
                    current_time = datetime.now()
                    time_difference = arrival_datetime - current_time
                    minutes, seconds = divmod(int(time_difference.total_seconds()), 60)
                    if minutes >= 0 and seconds >= 0:
                        subway_trains.append((minutes, seconds))
    return [f"Next Q {mins:2}m {secs:2}s" for mins, secs in sorted(subway_trains)[:limit]]

# Main function to fetch and display next buses and trains
def main():
    while True:
        try:
            subway_feed = fetch_gtfs_feed(SUBWAY_FEED_URL)
            all_buses = fetch_and_process_bus_data(API_KEY, BUS_STOP_ID, LINE_REFS)
            
            bus_output = process_bus_data(all_buses)
            train_output = process_subway_data(subway_feed)

            combined_output = '\n'.join(bus_output + train_output)
            send_to_arduino(combined_output)
            print(combined_output)  # Print the data to console, check against what Arduino displays
            print('END TRANSMISSION')

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(REFRESH_INTERVAL)  # Refresh the Arduino with new data every REFRESH_INTERVAL seconds

if __name__ == "__main__":
    main()
