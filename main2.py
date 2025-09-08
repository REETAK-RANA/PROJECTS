import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import json
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import requests
import time
import RPi.GPIO as GPIO

# Setup GPIO for relay control (example)
GPIO.setmode(GPIO.BCM)
relay_pin = 17
GPIO.setup(relay_pin, GPIO.OUT)

# MQTT & InfluxDB configuration
BROKER = "localhost"
TOPIC = "home/energy/#"
INFLUX_DB = 'home_energy'

influx_client = InfluxDBClient(host='localhost', port=8086)
influx_client.switch_database(INFLUX_DB)

# Placeholder for solar API config
SOLAR_API_KEY = 'YOUR_API_KEY'
LAT, LON = 'YOUR_LATITUDE', 'YOUR_LONGITUDE'
SOLAR_API_URL = f"http://api.openweathermap.org/data/2.5/solar_radiation?lat={LAT}&lon={LON}&appid={SOLAR_API_KEY}"

# Store incoming data for batch ML training
data_buffer = []

def fetch_solar_radiation():
    try:
        response = requests.get(SOLAR_API_URL)
        data = response.json()
        return data.get('solar_radiation', 0)
    except Exception as e:
        print("Solar API error:", e)
        return 0

def train_model(df):
    if len(df) < 10:
        print("Not enough data to train")
        return None
    df['hour'] = df.index.hour
    X = df[['hour']]
    y = df['value']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor()
    model.fit(X_train, y_train)
    print("Model trained with score:", model.score(X_test, y_test))
    return model

def control_devices(predicted_load, solar_radiation):
    threshold = 50  # Example threshold value
    min_solar = 10  # Min solar radiation threshold
    
    if predicted_load > threshold and solar_radiation < min_solar:
        print("Load high and solar low - Turning OFF devices")
        GPIO.output(relay_pin, GPIO.LOW)
    else:
        print("Conditions normal - Turning ON devices")
        GPIO.output(relay_pin, GPIO.HIGH)

def on_connect(client, userdata, flags, rc):
    print("Connected MQTT with result code "+str(rc))
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        value = float(payload['value'])
        sensor = msg.topic.split('/')[-1]
        json_body = [{
            "measurement": "energy_usage",
            "tags": {"sensor": sensor},
            "fields": {"value": value}
        }]
        influx_client.write_points(json_body)
        data_buffer.append({'time': pd.Timestamp.now(), 'value': value})

        # Periodically train model and control devices
        if len(data_buffer) >= 20:
            df = pd.DataFrame(data_buffer).set_index('time')
            model = train_model(df)
            if model:
                current_hour = pd.Timestamp.now().hour
                predicted_load = model.predict([[current_hour]])[0]
                solar_rad = fetch_solar_radiation()
                control_devices(predicted_load, solar_rad)
            data_buffer.clear()

    except Exception as e:
        print("Error processing message:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883, 60)

try:
    print("Starting MQTT client loop")
    client.loop_forever()
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
