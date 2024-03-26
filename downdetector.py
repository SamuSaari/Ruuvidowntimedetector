import requests
import os
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta
import pytz

# Pushover Parameters
pushover_user_key = os.getenv('S_RDTD_PUSHOVER_USER_KEY')
pushover_api_token = os.getenv('S_RDTD_PUSHOVER_API_TOKEN')
influxdb_url = os.getenv('INFLUXDB_URL')
influxdb_token = os.getenv('S_RDTD_INFLUXDB_TOKEN')
influxdb_org = os.getenv('INFLUXDB_ORG')
influxdb_bucket = os.getenv('S_RDTD_INFLUXDB_BUCKET')
measurement_name = 'ruuvitag'

# Function to send Pushover notification
def send_pushover_notification(message):
    url = 'https://api.pushover.net/1/messages.json'
    data = {
        'token': pushover_api_token,
        'user': pushover_user_key,
        'message': message
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Notification sent successfully.")
    else:
        print("Failed to send notification.")

# Connect to InfluxDB 2.x
client = InfluxDBClient(url="https://influx.mittauslaskenta.com", token=influxdb_token, org=influxdb_org)
query_api = client.query_api()


device_ids = ['Gummeruksenkatu', 'Honor_1', 'Samsung', 'kilpisenkatu']
alert_threshold_minutes = 20  # Alert if no data in the last X minutes

# Initialize an empty list to store messages
messages = []

for device_id in device_ids:
    # Modify your query to include filtering for the current device_id
    query = f'''
    from(bucket: "Ruuvi_Database")
      |> range(start: -{alert_threshold_minutes}m)
      |> filter(fn: (r) => r["_measurement"] == "ruuvitag")
      |> filter(fn: (r) => r["_field"] == "temperature")
      |> filter(fn: (r) => r["deviceID"] == "{device_id}")
      |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
      |> yield(name: "mean")
    '''

    result = query_api.query(query)

    # Assuming the latest point is what we're interested in
    points = [point for table in result for point in table.records]

    if not result or not points:
        # No data for this device at all
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current time and format it as a string
        message = f"No data points found for device {device_id} in the last {alert_threshold_minutes} minutes. Current time: {now}"
        messages.append(message)
    else:
        print(device_id + " has data points in the last " + str(alert_threshold_minutes) + " minutes.")

# If there are any messages, join them into a single string and send a notification
if messages:
    now = datetime.now()
    last_notification_time = None

    # Try to read the time of the last notification from a file
    try:
        with open('last_notification_time.txt', 'r') as f:
            last_notification_time = datetime.strptime(f.read(), '%Y-%m-%d %H:%M:%S')
    except FileNotFoundError:
        pass  # It's okay if the file doesn't exist

    # Check if any of the messages indicate that data was found
    data_found = any("has data points" in message for message in messages)

    # Only send a notification if enough time has passed since the last one, or if data was found
    if data_found or last_notification_time is None or now - last_notification_time > timedelta(minutes=10):
        message = "\n\n".join(messages)
        send_pushover_notification(message)

        # Write the time of this notification to a file
        with open('last_notification_time.txt', 'w') as f:
            f.write(now.strftime('%Y-%m-%d %H:%M:%S'))