# DownDetector

This script checks if there are any data points for specific devices in an InfluxDB database within a certain time threshold. If no data points are found for a device within the threshold, a notification is sent via Pushover.

## Requirements

- Python 3
- `requests`
- `influxdb_client`
- `pytz`

You can install the required Python packages with pip:

```bash
pip install requests influxdb_client pytz