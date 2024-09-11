# Device Temperature Monitoring Application

This is a Flask-based web application that monitors temperature sensors, stores their data in Redis, and allows configuration of devices. The application can send alerts when the temperature exceeds a certain threshold and enables/disables alerts for specific devices.

## Features

- **Device Listing**: Lists all temperature devices stored in Redis.
- **Device Configuration**: Allows the user to configure individual devices, including setting a maximum temperature threshold and alert frequency.
- **Temperature Monitoring**: Checks the current temperature of the devices and compares it with the maximum allowed threshold.
- **Alerts**: Sends alerts if the temperature exceeds the maximum value, and allows for configuring the alert interval and enabling/disabling alerts.
- **Redis Integration**: All device data (names, temperatures, alert settings) is stored in Redis.

## Prerequisites

- **Python 3.x**
- **Flask** (Web framework)
- **Redis** (Database for storing device information)
- **redis-py** (Python client for Redis)
- **Jinja2** (Template engine, part of Flask)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/restoore/your-repo.git
   cd your-repo
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Redis on your machine if it's not already installed:
   - On macOS: `brew install redis`
   - On Linux: `sudo apt-get install redis-server`
   - On Windows: [Install Redis for Windows](https://github.com/microsoftarchive/redis/releases)

4. Start the Redis server:
   ```bash
   redis-server
   ```

5. Run the Flask app:
   ```bash
   python app.py
   ```

6. Access the application in your browser at `http://localhost:5000`.

## Redis Configuration

Before running the application, you need to configure the connection to your Redis instance. A sample configuration file is provided in the repository under the name `config.sample.yml`. You should rename this file to `config.yml` and fill in the correct details for your Redis server.

### Steps:

1. Rename the file:
   ```bash
   mv config.sample.yml config.yml
   ```

2. Edit the `config.yml` file and replace the placeholder values with your actual Redis server's details:

```yaml
redis:
  host: 'example-redis.cache.windows.net'
  access-key: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

- **`host`**: The hostname of your Redis instance (e.g., a managed Redis instance on a cloud provider).
- **`access-key`**: The access key or password to authenticate with your Redis instance.

The application will use this configuration to connect to Redis for storing and retrieving device data.

## Application Structure

```
.
├── app.py               # Main application file (Flask routes and logic)
├── templates/
│   ├── base.html        # Base template with common structure
│   ├── device_form.html # Device configuration form page
│   ├── device_list.html # Device listing page
│   ├── footer.html      # Reusable footer template with version info
├── static/
│   ├── css/             # Optional: Static CSS files
│   └── js/              # Optional: Static JS files
├── requirements.txt     # Python dependencies
├── README.md            # Project README file
└── .gitignore           # Files to ignore in Git
```

## Routes and Endpoints

### 1. `/devices`
- **Description**: Lists all devices stored in Redis.
- **Method**: `GET`
- **Logic**: 
  - Fetches device data from Redis.
  - Displays a list of devices with options to configure each one.

### 2. `/device/<int:device_id>`
- **Description**: Displays the configuration page for an individual device.
- **Method**: `GET` / `POST`
- **Logic**: 
  - **GET**: Retrieves the current configuration and temperature of the device from Redis.
  - **POST**: Updates the device configuration (e.g., maximum temperature, alert frequency, and whether alerts are enabled).
  
### 3. `/device-list` and `/list-devices`
- **Description**: Alternative routes to view the list of devices.
- **Method**: `GET`
- **Logic**: These routes point to the same function as `/devices`, allowing multiple URLs to access the same functionality.

## Redis Keys

The application uses Redis to store device data. Each device is represented by the following keys:

- `alert_<device_id>_name`: The name of the device (e.g., "Fridge").
- `alert_<device_id>_curr_temp`: The current temperature of the device.
- `alert_<device_id>_max_temp`: The maximum temperature threshold for alerts.
- `alert_<device_id>_time_next`: The datetime of the next allowed alert.
- `alert_<device_id>_enabled`: Whether alerts are enabled (`1` for enabled, `0` for disabled).

### Example Redis Key for Device 49671:
```
alert_49671_name      -> "Fridge"
alert_49671_curr_temp -> "5.6"
alert_49671_max_temp  -> "10"
alert_49671_enabled   -> "1"
alert_49671_time_next -> "2024-09-10 14:00:00"
```

## Monitoring Temperature and Sending Alerts

### Function: `is_max_temperature`

The function `is_max_temperature` checks the current temperature of a device and sends an alert if the temperature exceeds the maximum threshold.

```python
def is_max_temperature(self, config, subdevice: TemperatureAirSensor, max_temp: int = 34) -> None:
    # Verify if alerts are enabled for this device
    alert_enabled = self.get_cache(f"alert_{subdevice.did}_enabled")
    
    if alert_enabled != '1':
        logger.info(f"Alerts are disabled for device {subdevice.name}. Skipping check.")
        return
    
    # Calculate current temperature
    curr_temp = subdevice.temp_mk_current * 1e-3 - 273.15
    logger.info(f"Checking max temperature for device {subdevice.name}, current: {curr_temp}, max allowed: {max_temp}")

    # If current temperature exceeds the maximum
    if curr_temp >= subdevice.max_temperature:
        # Send alert and update Redis with next alert time
        self.send_alert_and_update_cache(subdevice, curr_temp)
```

**Alert Logic**:
- The function first checks if the alert is enabled for the device by retrieving `alert_<device_id>_enabled` from Redis.
- If the current temperature exceeds the maximum threshold (`max_temperature`), an alert is triggered, and the time for the next allowed alert is updated in Redis (`alert_<device_id>_time_next`).

## Templates

### `base.html`
A common layout template used by other pages, containing the structure of the header, body, and footer.

```html
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}My Application{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container py-5">
        {% block content %}{% endblock %}
    </div>
    {% include 'footer.html' %}
</body>
</html>
```

### `footer.html`
A reusable footer containing version information and a link to your GitHub profile.

```html
<footer class="bg-light text-center py-4 mt-5">
    <div class="container">
        <p class="mb-0">Version: {{ version }}</p>
        <p>
            <a href="https://github.com/restoore" target="_blank">Visit my GitHub</a>
        </p>
    </div>
</footer>
```

### `device_list.html`
Displays the list of devices stored in Redis.

```html
<ul class="list-group">
    {% for device in devices %}
    <li class="list-group-item d-flex justify-content-between align-items-center">
        <span>{{ device.device_name }}</span>
        <a href="/device/{{ device.device_id }}" class="btn btn-primary btn-sm">Configure</a>
    </li>
    {% else %}
    <li class="list-group-item text-center">No devices available</li>
    {% endfor %}
</ul>
```

### `device_form.html`
Displays the configuration form for an individual device.

```html
<form method="POST" action="/device/{{ device_id }}">
    <label for="deviceName">Device Name</label>
    <input type="text" id="deviceName" name="deviceName" value="{{ device_name }}">
    
    <label for="maxTemperature">Maximum Temperature (°C)</label>
    <input type="range" id="maxTemperature" name="maxTemperature" value="{{ max_temp }}">
    
    <button type="submit">Submit</button>
</form>
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.