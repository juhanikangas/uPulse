import network
import time
import ujson
from umqtt.simple import MQTTClient


#     SSID = 'KMD657_GROUP_1'
#     PASSWORD = 'q1w2e3r4t5'    
#     BROKER_IP = '192.168.1.253'

SSID = "AirPort_Extreme_Ultima"
PASSWORD = "signumss2911"
BROKER_IP = "10.0.01.33"
CLIENT_ID = 'pico'
PUBLISH_TOPIC = "pico/output"
SUBSCRIBE_TOPIC = "backend/output"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    print("Connected to WiFi\nIP:", wlan.ifconfig()[0])

def on_message(topic, msg):
    global response
    print("Received message:", msg.decode())
    response = msg.decode()

def make_request(body):
    global response
    response = None  # Reset response each time
    connect_wifi()
    mqtt_client = MQTTClient(CLIENT_ID, BROKER_IP, keepalive=60)
    mqtt_client.set_callback(on_message)

    try:
        mqtt_client.connect()
        mqtt_client.subscribe(SUBSCRIBE_TOPIC)
        print("Subscribed to:", SUBSCRIBE_TOPIC)

        message = ujson.dumps(body)
        mqtt_client.publish(PUBLISH_TOPIC, message)
        print("Message sent:", message)

        start_time = time.time()
        timeout = 7  # seconds
        while response is None:
            mqtt_client.check_msg()
            if time.time() - start_time > timeout:
                response = "timeout"
                break
            time.sleep(0.1)
    except Exception as e:
        print(f"Error during MQTT communication: {e}")
    finally:
        mqtt_client.disconnect()
        print("Disconnected from MQTT broker.")

    return response

