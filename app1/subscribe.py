import os
import django
from datetime import datetime
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pilot_feedtray.settings')
django.setup()

import paho.mqtt.client as mqtt
from app1.models import Cycle

# MQTT Configuration
MQTT_BROKER = 'mqttbroker.bc-pl.com'
MQTT_PORT = 1883
MQTT_TOPIC_END = 'feeder/fdtryA00/cycle_status'
MQTT_USER = 'mqttuser'
MQTT_PASSWORD = 'Bfl@2025'

# Mark cycle completion
def mark_cycle_completed():
    try:
        latest = Cycle.objects.latest('timestamp')
        latest.end_time = datetime.now()
        latest.save()
        print(f"[✓] Cycle ID {latest.id} marked as completed at {latest.end_time}")
    except Exception as e:
        print("[!] Error marking cycle end:", e)

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print("[✓] Connected with result code", rc)
    client.subscribe(MQTT_TOPIC_END)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode().strip()
    print(f"[→] Message on topic {topic}: {payload}")

    if topic == MQTT_TOPIC_END and payload.lower() == 'all cycle completed':
        mark_cycle_completed()
    else:
        print("[i] Ignored message:", payload)

# Setup MQTT client
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
