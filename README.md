# NextTransit

NextTransit is a Python application that displays the next bus and subway arrivals on an Arduino Uno. It fetches real-time data from the MTA API for buses and GTFS feeds for subways, processes the data, and sends the information to an Arduino connected via a serial port. Yes, this ReadME was also created using ChatGPT

## Features

- Fetches real-time bus data from the MTA API.
- Fetches real-time subway data from GTFS feeds.
- Displays next arrival times for buses and subways on an Arduino Uno.
- Customizable to track specific bus lines and subway stops.

## Prerequisites

- Python 3.x
- Arduino Uno with appropriate display setup
- MTA API key

## Usage Notes
- Bus Stops: Visit [MTA Bus Time](https://bustime.mta.info) to find your bus stop, or look IRL at your local bus stop.
- Subway Stops: You can find subway stops at [data.gov.](https://catalog.data.gov/dataset/mta-subway-stations-and-complexes) Note that you need to specify the direction for subway stops (e.g., Q03S for southbound and Q03N for northbound).
