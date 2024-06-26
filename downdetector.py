import requests
import os
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from pytz import timezone

# Set the timezone
helsinki_tz = timezone('Europe/Helsinki')


# Env variables
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
client = InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)
query_api = client.query_api()


device_ids = ['Gummeruksenkatu', 'Honor_1', 'Samsung', 'kilpisenkatu']
alert_threshold_minutes = 20  # Alert if no data in the last X minutes

# Initialize an empty list to store messages
messages = []



for device_id in device_ids:
    # Get the current time in your local timezone
    now = datetime.now(timezone('Europe/Helsinki'))
    # Calculate the start time
    start_time = now - timedelta(minutes=alert_threshold_minutes)
    start_time_str = start_time.isoformat()
    now_str = now.isoformat()
    # Modify your query to include filtering for the current device_id
    query = f'''
    from(bucket: "{influxdb_bucket}")
    |> range(start: {start_time_str}, stop: {now_str})
    |> filter(fn: (r) => r["_measurement"] == "{measurement_name}")
    |> filter(fn: (r) => r["_field"] == "temperature")
    |> filter(fn: (r) => r["deviceID"] == "{device_id}")
    '''
    print(f"Executing query: {query}")  # Print the query for debugging

    result = query_api.query(query)

     # Assuming the latest point is what we're interested in
    points = [point for table in result for point in table.records]

    if not result or not points:
        # No data for this device at all
        now = datetime.now(helsinki_tz).strftime('%Y-%m-%d %H:%M:%S')  # Get the current time in Helsinki timezone and format it as a string
        message = f"No data points found for device {device_id} in the last {alert_threshold_minutes} minutes. Current time: {now}"
        messages.append(message)
    else:
        print(device_id + " has data points in the last " + str(alert_threshold_minutes) + " minutes.")
        
# If there are any messages, join them into a single string and send a notification
if messages:
    now = datetime.now(helsinki_tz)
    last_notification_time = None

    # Try to read the time of the last notification from a file
    try:
        with open('last_notification_time.txt', 'r') as f:
            last_notification_time_str = f.read().strip()  # Remove leading and trailing whitespace and newlines
            last_notification_time = datetime.strptime(last_notification_time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=helsinki_tz)
    except FileNotFoundError:
        pass  # It's okay if the file doesn't exist

    # Check if any of the messages indicate that data was found
    data_found = any("has data points" in message for message in messages)

    # Only send a notification if enough time has passed since the last one, or if data was found
    if data_found or last_notification_time is None or now - last_notification_time > timedelta(minutes=60):
        message = "\n\n".join(messages)
        send_pushover_notification(message)

        # Write the time of this notification to a file
        with open('last_notification_time.txt', 'w') as f:
            f.write(now.strftime('%Y-%m-%d %H:%M:%S'))