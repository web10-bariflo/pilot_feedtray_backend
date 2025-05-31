# subscribe.py

import os
import django
import paho.mqtt.client as mqtt
from django.utils.timezone import now

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pilot_feedtray.settings")
django.setup()

from app1.models import MQTTMessage, Cycle

MQTT_BROKER = 'mqttbroker.bc-pl.com'
MQTT_PORT = 1883
MQTT_USER = 'mqttuser'
MQTT_PASSWORD = 'Bfl@2025'

MQTT_TOPICS = ['feeder/+/weight_initial']

device_cycle_tracker = {}
device_data = {}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker.")
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print(f"📡 Subscribed to: {topic}")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8').strip()
        topic_parts = msg.topic.split('/')
        device_id = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
        topic_name = topic_parts[2] if len(topic_parts) > 2 else 'unknown'

        if topic_name == 'weight_initial':
            try:
                weight_value = float(payload)
            except ValueError:
                print(f"❌ Invalid weight value: {payload}")
                return

            if device_id not in device_data and weight_value < 5:
                print(f"⛔ Reject: New device {device_id} must start with weight_initial >= 5. Received: {weight_value}")
                return

            latest_global = MQTTMessage.objects.order_by('-timestamp').first()
            if latest_global and latest_global.weight_final == 1.0 and weight_value < 5:
                print(f"⛔ Global lock: Last final weight was 1.0. Cannot accept < 5 for {device_id}")
                return

            latest_cycle = Cycle.objects.filter(device_id=device_id).order_by('-id').first()
            if latest_cycle:
                try:
                    latest_remaining = float(latest_cycle.remaining)
                except Exception:
                    latest_remaining = None
                if latest_remaining == 1.0 and weight_value < 5:
                    print(f"⛔ Device lock: Device {device_id} trying < 5 when remaining = 1")
                    return

            device = device_data.setdefault(device_id, {
                'weight_initial': None,
                'weight_final': None,
                'allow_new_weight': True,
            })

            current_cycle = device_cycle_tracker.get(device_id, 1)

            if not device['allow_new_weight'] and weight_value < 5:
                print(f"⛔ Reject: {device_id} sent weight_initial < 5 after final = 1.0")
                return

            if device['weight_initial'] is None or weight_value != float(device['weight_initial']):
                device_cycle_tracker[device_id] = current_cycle + 1
                current_cycle = device_cycle_tracker[device_id]
                print(f"🔄 New cycle {current_cycle} started for {device_id}")

            device['weight_initial'] = weight_value
            device['weight_final'] = None
            device['allow_new_weight'] = True

            MQTTMessage.objects.create(
                device_id=device_id,
                topic=msg.topic,
                weight_intial=str(weight_value),
                weight_final=None,
                cycle_number=current_cycle,
                timestamp=now()
            )

            print(f"✅ Saved: {device_id} | weight_initial={weight_value} | cycle={current_cycle}")

    except Exception as e:
        print(f"❌ Error handling message: {e}")

def start_mqtt_subscriber():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"❌ Subscriber error: {e}")

if __name__ == "__main__":
    start_mqtt_subscriber()
