from google.transit import gtfs_realtime_pb2
from datetime import datetime, timedelta

import requests
import serial
import time

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

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Bus class to encapsulate bus information
class Bus:
    def __init__(self, est_arrival, bus_type):
        self.est_arrival = est_arrival
        self.bus_type = bus_type

    def get_time_difference(self):
        future_time_str = self.est_arrival[11:19] ##ISO8601 (eg 2015-06-04T10:46:08.361-04:00) format spliced to obtain time
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
        ser = serial.Serial('COM3', 9600, timeout=1)  # Replace 'COM3' with your port name
        time.sleep(2)  # Wait for the connection to establish
        ser.write(data.encode())
        ser.close()
    except serial.SerialException as e:
        print(f"Error: {e}")

# Main function to fetch and display next buses and trains
def main():
    while True:
        # URL for GTFS real-time subway feed
        subway_feed_url = 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw'
        subway_feed = fetch_gtfs_feed(subway_feed_url)

        # Bus API credentials and stop information
        api_key = "YOUR_API_KEY_HERE" 
        stop_id = "MTA_401756" ##Add your stop_id here

        line_refs = ["MTA NYCT_M15", "MTA NYCT_M15+"] ## M15 and M15-SBS serve my stop

        try:
            # Fetch and process bus data
            all_buses = []
            for line_ref in line_refs:
                data = get_stop_monitoring(api_key, stop_id, line_ref)
                bus_data = data['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']

                buses = []
                for visit in bus_data:
                    est_arrival = visit['MonitoredVehicleJourney']['MonitoredCall'].get('ExpectedArrivalTime', None)
                    if est_arrival:
                        bus_type = visit['MonitoredVehicleJourney']['PublishedLineName']
                        bus = Bus(est_arrival, bus_type)
                        buses.append(bus)

                all_buses.extend(buses)

            # Process and print ranked list of buses (limit to 2)
            ranked_buses = sorted(all_buses, key=lambda bus: bus.get_time_difference())[:2]
            bus_output = []
            for bus in ranked_buses:
                minutes, seconds = bus.get_time_difference()
                if minutes >= 0 and seconds >= 0:
                    bus_type_short = (bus.bus_type[:8] + '..') if len(bus.bus_type) > 8 else bus.bus_type
                    bus_output.append(f"{bus_type_short:<8} {minutes:2}m {seconds:2}s")

            # Process and print subway data (limit to 2)
            subway_trains = []
            for entity in subway_feed.entity:
                if entity.HasField('trip_update'):
                    for stop_time_update in entity.trip_update.stop_time_update:
                        if stop_time_update.stop_id == 'Q03S':
                            arrival_timestamp = stop_time_update.arrival.time
                            arrival_datetime = datetime.fromtimestamp(arrival_timestamp, tz=None)
                            current_time = datetime.now()
                            time_difference = arrival_datetime - current_time
                            minutes, seconds = divmod(int(time_difference.total_seconds()), 60)
                            if minutes >= 0 and seconds >= 0:
                                subway_trains.append((minutes, seconds))

            train_output = []
            for mins, secs in sorted(subway_trains)[:2]:
                train_output.append(f"Next Q {mins:2}m {secs:2}s")

            # Combine and send data to Arduino
            combined_output = '\n'.join(bus_output + train_output)
            send_to_arduino(combined_output)
            print(combined_output) ##Print the data to console, check against what arduino displays
            print('END TRANSMISSION')

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(10) ##Refresh the Arduino with new code every 10 seconds

if __name__ == "__main__":
    main()