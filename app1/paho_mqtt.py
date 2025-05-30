# import os
# import time
# import re
# import django
# import paho.mqtt.client as mqtt
# from django.utils.timezone import now
# from app1.models import MQTTMessage

# MQTT_BROKER = 'mqttbroker.bc-pl.com'
# MQTT_PORT = 1883
# MQTT_USER = 'mqttuser'
# MQTT_PASSWORD = 'Bfl@2025'

# MQTT_TOPICS = [
#     'feeder/fdtryA00/cycle_status',
#     'feeder/fdtryA00/weight_initial',
#     'feeder/fdtryA00/weight_final',
# ]

# device_cycle_tracker = {}   # Tracks current cycle number per device
# device_cycle_buffer = {}    # Buffers messages until a full cycle is complete

# def extract_cyclecount(payload):
#     match = re.search(r'cycle(?:count)?\s*=\s*(\d+)', payload, re.I)
#     if match:
#         return match.group(1)
#     match = re.search(r'=\s*(\d+)', payload)
#     if match:
#         return match.group(1)
#     return None

# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("✅ Connected to MQTT broker.")
#         for topic in MQTT_TOPICS:
#             client.subscribe(topic)
#             print(f"📡 Subscribed to: {topic}")
#     else:
#         print(f"❌ MQTT connection failed with code {rc}")

# def on_message(client, userdata, msg):
#     try:
#         timestamp = now()
#         payload = msg.payload.decode('utf-8').strip()
#         topic_parts = msg.topic.split('/')
#         device_id = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
#         topic_name = topic_parts[2] if len(topic_parts) > 2 else 'unknown'
#         cyclecount = extract_cyclecount(payload)

#         # Initialize cycle number
#         if device_id not in device_cycle_tracker:
#             device_cycle_tracker[device_id] = 1

#         current_cycle = device_cycle_tracker[device_id]

#         # Initialize buffer if needed
#         if device_id not in device_cycle_buffer:
#             device_cycle_buffer[device_id] = {
#                 'weight_initial': None,
#                 'cycle_status': [],
#                 'weight_final': None,
#             }

#         buffer = device_cycle_buffer[device_id]

#         # Update buffer
#         if topic_name == 'weight_initial':
#             buffer['weight_initial'] = payload
#         elif topic_name == 'cycle_status':
#             buffer['cycle_status'].append(payload.lower())
#         elif topic_name == 'weight_final':
#             buffer['weight_final'] = payload

#         # Save to DB with current cycle number
#         MQTTMessage.objects.create(
#             device_id=device_id,
#             topic=topic_name,
#             payload=payload,
#             timestamp=timestamp,
#             cycle_number=current_cycle,
#             cyclecount=cyclecount
#         )

#         print(f"✅ Saved: {device_id} | Cycle {current_cycle} | {topic_name} | {payload}")

#         # Check if cycle is completed
#         if (
#             buffer['weight_initial'] is not None and
#             any('initial' in s for s in buffer['cycle_status']) and
#             any('running' in s for s in buffer['cycle_status']) and
#             any('completed' in s for s in buffer['cycle_status']) and
#             buffer['weight_final'] is not None
#         ):
#             print(f"🔁 Cycle {current_cycle} completed for {device_id}")

#             # Prepare for next cycle
#             device_cycle_tracker[device_id] = current_cycle + 1
#             device_cycle_buffer[device_id] = {
#                 'weight_initial': None,
#                 'cycle_status': [],
#                 'weight_final': None,
#             }

#     except Exception as e:
#         print(f"❌ Error: {e}")

# def mqtt_connect():
#     client = mqtt.Client()
#     client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
#     client.on_connect = on_connect
#     client.on_message = on_message

#     try:
#         client.connect(MQTT_BROKER, MQTT_PORT, 60)
#     except Exception as e:
#         print(f"❌ Failed to connect to broker: {e}")
#         return

#     client.loop_start()
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("⛔ Stopped.")
#         client.loop_stop()
#         client.disconnect()

# if __name__ == "__main__":
#     mqtt_connect()





import os
import time
import re
import django
import paho.mqtt.client as mqtt
from django.utils.timezone import now

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")  # Change to your actual project name
django.setup()

from app1.models import MQTTMessage  # Import after Django setup

MQTT_BROKER = 'mqttbroker.bc-pl.com'
MQTT_PORT = 1883
MQTT_USER = 'mqttuser'
MQTT_PASSWORD = 'Bfl@2025'

MQTT_TOPICS = [
    'feeder/fdtryA00/cycle_status',
    'feeder/fdtryA00/weight_initial',
    'feeder/fdtryA00/weight_final',
]

device_cycle_tracker = {}
device_cycle_buffer = {}

def extract_cyclecount(payload):
    match = re.search(r'cycle(?:count)?\s*=\s*(\d+)', payload, re.I)
    if match:
        return match.group(1)
    match = re.search(r'=\s*(\d+)', payload)
    return match.group(1) if match else None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker.")
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print(f"📡 Subscribed to: {topic}")
    else:
        print(f"❌ MQTT connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        timestamp = now()
        payload = msg.payload.decode('utf-8').strip()
        topic_parts = msg.topic.split('/')
        device_id = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
        topic_name = topic_parts[2] if len(topic_parts) > 2 else 'unknown'

        # Parse weight_initial payload to float if possible
        weight_value = None
        if topic_name == 'weight_initial':
            try:
                weight_value = float(payload)
            except ValueError:
                pass  # Not a valid float, ignore or handle

        # Initialize cycle tracker if not exists
        current_cycle = device_cycle_tracker.get(device_id, 1)
        buffer = device_cycle_buffer.setdefault(device_id, {
            'weight_initial': None,
            'cycle_status': [],
            'weight_final': None,
        })

        # Warning on weight_initial = 5kg
        if topic_name == 'weight_initial':
            if weight_value == 5.0:
                print(f"⚠️ Warning: weight_initial is 5 kg for device {device_id} at cycle {current_cycle}")

            # Cycle completion condition
            if weight_value == 1.0:
                print(f"✅ Cycle {current_cycle} completed for device {device_id}")

                # After completion, increment cycle count and reset buffer
                device_cycle_tracker[device_id] = current_cycle + 1
                device_cycle_buffer[device_id] = {
                    'weight_initial': None,
                    'cycle_status': [],
                    'weight_final': None,
                }
                current_cycle = device_cycle_tracker[device_id]

            else:
                # Update current cycle's weight_initial
                buffer['weight_initial'] = payload

        elif topic_name == 'cycle_status':
            buffer['cycle_status'].append(payload.lower())
        elif topic_name == 'weight_final':
            buffer['weight_final'] = payload

        # Save message with current cycle count
        MQTTMessage.objects.create(
            device_id=device_id,
            topic=topic_name,
            payload=payload,
            timestamp=timestamp,
            cycle_number=current_cycle
        )

        print(f"Saved: {device_id} | Cycle {current_cycle} | {topic_name} | {payload}")

    except Exception as e:
        print(f"Error: {e}")


def mqtt_connect():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("⛔ Stopped.")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    mqtt_connect()
