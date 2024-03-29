# DownDetector

This script checks if there are any data points for specific devices in an InfluxDB database within a certain time threshold. If no data points are found for a device within the threshold, a notification is sent via Pushover.

## Requirements

- Python 3
- `requests`
- `influxdb_client`
- `pytz`

You can install the required Python packages with pip:

    pip install requests influxdb_client pytz

## Environment Variables

The script requires the following environment variables:

- `S_RDTD_PUSHOVER_USER_KEY`: Your Pushover user key.
- `S_RDTD_PUSHOVER_API_TOKEN`: Your Pushover API token.
- `INFLUXDB_URL`: The URL of your InfluxDB instance.
- `S_RDTD_INFLUXDB_TOKEN`: Your InfluxDB token.
- `INFLUXDB_ORG`: Your InfluxDB organization.
- `S_RDTD_INFLUXDB_BUCKET`: The InfluxDB bucket to query.

## Usage

Run the script with Python:

    python downdetector.py

The script will check for data points for the devices specified in the device_ids list within the last alert_threshold_minutes minutes. If no data points are found for a device, a notification will be sent.

The time of the last notification is stored in a file named `last_notification_time.txt`. A new notification will only be sent if at least 60 minutes have passed since the last notification, or if data points are found for a device.