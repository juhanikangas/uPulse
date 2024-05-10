import requests
import json
import os
import time
from paho.mqtt.client import Client as MQTTClient

# Constants
APIKEY = ""
CLIENT_ID = ""
CLIENT_SECRET = ""
TOKEN_URL = ""
#BROKER_IP = ""
BROKER_IP = ""
SUBSCRIBE_TOPIC = "pico/output"
PUBLISH_TOPIC = "backend/output"
JSON_DB_FILE = "kubios_results.json"

mqtt_client = None  # Global variable to store the MQTT client

def get_token():
    try:
        response = requests.post(
            TOKEN_URL,
            data=f'grant_type=client_credentials&client_id={CLIENT_ID}',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            auth=(CLIENT_ID, CLIENT_SECRET)
        )
        response.raise_for_status()  # Check for HTTP errors
        return response.json().get("access_token")
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def analyze_data(token, dataset):
    try:
        response = requests.post(
            "https://analysis.kubioscloud.com/v2/analytics/analyze",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Api-Key": APIKEY,
                "Cache-Control": "no-cache"
            },
            json=dataset
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error analyzing data: {e}")
        return None

def save_result_to_file(result, filename=JSON_DB_FILE):
    try:
        data = []
        if os.path.exists(filename):
            with open(filename, "r") as file:
                data = json.load(file)
        data.append(result)
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Saved result to {filename}")
    except Exception as e:
        print("Error saving result:", e)

def history(message):
    index = message["data"]
    try:
        with open(JSON_DB_FILE, "r") as f:
            history_data = json.load(f)
        history_data.reverse()

        if index < 0 or index >= len(history_data):
            print("Index out of range")
            return

        history_data_str = json.dumps(history_data[index]).encode()
        mqtt_client.publish(PUBLISH_TOPIC, history_data_str)
        print(f"Published to {PUBLISH_TOPIC}: {history_data[index]}")

    except Exception as e:
        print("Error reading JSON file:", e)


def timestamps():
    try:
        with open(JSON_DB_FILE, "r") as f:
            history_data = json.load(f)
        timestamps = []

        for item in history_data:
            if 'analysis' in item and 'create_timestamp' in item['analysis']:
                timestamps.append(item['analysis']['create_timestamp'])
        
        timestamps.reverse()
        timestamps_str = json.dumps(timestamps).encode()
            
        mqtt_client.publish(PUBLISH_TOPIC, timestamps_str)
        print(f"Published to {PUBLISH_TOPIC}: {timestamps_str}")

    except Exception as e:
        print("Error reading JSON file or processing data:", e)




def kubios(message):
    intervals = message["data"]
    dataset = {
        "type": "RRI",
        "data": intervals,
        "analysis": {"type": "readiness"}
    }
    token = get_token()
    if token:
        analysis_result = analyze_data(token, dataset)
        if analysis_result:
            print("Analysis Result:", analysis_result)
            analysis_result_str = json.dumps(analysis_result).encode()
            mqtt_client.publish(PUBLISH_TOPIC, analysis_result_str)
            print(f"Published to {PUBLISH_TOPIC}: {analysis_result}")
            save_result_to_file(analysis_result)

def on_message(client, userdata, msg):
    print("Received message on topic:", msg.topic)
    try:
        message = json.loads(msg.payload.decode())
        print("Message data:", message)
        if message["type"] == "kubios":
            kubios(message)
        elif message["type"] == "history":
            history(message)
        elif message["type"] == "timestamps":
            timestamps()
    except Exception as e:
        print("Error processing message:", e)

def main():
    try:
        global mqtt_client
        mqtt_client = MQTTClient(CLIENT_ID)
        mqtt_client.on_message = on_message
        print("Connecting to broker:", BROKER_IP)
        mqtt_client.connect(BROKER_IP)
        print("Subscribing to topic:", SUBSCRIBE_TOPIC)
        mqtt_client.subscribe(SUBSCRIBE_TOPIC)
        print("Server is running...")
        mqtt_client.loop_forever() 
    except Exception as e:
        print(f"Error setting up MQTT: {e}")
if __name__ == "__main__":
    main()