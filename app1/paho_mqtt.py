# ## old code dont delete it 


# import os
# import django
# import paho.mqtt.client as mqtt
# from django.utils.timezone import now

# # # Set up Django environment
# # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pilot_feedtray.settings")
# # django.setup()

# from app1.models import MQTTMessage, Cycle

# MQTT_BROKER = 'mqttbroker.bc-pl.com'
# MQTT_PORT = 1883
# MQTT_USER = 'mqttuser'
# MQTT_PASSWORD = 'Bfl@2025'


# MQTT_TOPICS = [
#     'feeder/fdtryA00/weight_initial',
#     'feeder/fdtryA00/weight_final',
#     'feeder/fdtryA00/cycle_status',
# ]

# device_cycle_tracker = {}  # Tracks current cycle number per device
# device_data = {}           # Holds per-device state


# def frontend_cycle_input(device_id, cyclecount):
#     device = device_data.get(device_id)
#     if not device or device['weight_initial'] is None:
#         print(f"❌ No initial weight available for device {device_id}")
#         return

#     weight_initial = float(device['weight_initial'])
#     weight_final = weight_initial - float(cyclecount)
#     timestamp = now()
#     current_cycle = device_cycle_tracker.get(device_id,0)

#     MQTTMessage.objects.create(
#         device_id=device_id,
#         topic='cyclecount',
#         weight_intial=str(weight_initial),
#         weight_final=str(weight_final),
#         cyclecount=str(cyclecount),
#         cycle_number=current_cycle,
#         timestamp=timestamp,
#     )

#     print(f"✅ Saved cycle data | Device: {device_id} | Cycle: {current_cycle} | Initial: {weight_initial} | Final: {weight_final} | Count: {cyclecount}")

#     device['weight_final'] = weight_final
#     if weight_final == 1.0:
#         device['allow_new_weight'] = False
#         print(f"⚠️ Device {device_id}: Final weight reached 1.0. No further weight_initial < 5 will be processed.")


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
#         payload = msg.payload.decode('utf-8').strip()
#         topic_parts = msg.topic.split('/')
#         device_id = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
#         topic_name = topic_parts[2] if len(topic_parts) > 2 else 'unknown'

#         if topic_name == 'weight_initial':
#             try:
#                 weight_value = float(payload)
#             except ValueError:
#                 print(f"❌ Invalid weight value: {payload}")
#                 return

#             # ✅ Reject if new device tries to send weight_initial < 5
#             if device_id not in device_data and weight_value < 5:
#                 print(f"⛔ MQTT reject: New device {device_id} must start with weight_initial >= 5. Received: {weight_value}")
#                 return

#             # ✅ Global restriction: block all weight_initial < 5 if last weight_final was 1.0
#             latest_global = MQTTMessage.objects.order_by('-timestamp').first()
#             if latest_global and latest_global.weight_final == 1.0 and weight_value < 5:
#                 print(f"⛔ MQTT reject: System locked. Last weight_final = 1.0, cannot accept new weight_initial < 5 (device: {device_id})")
#                 return

#             # ✅ Per-device restriction via Cycle.remaining
#             latest_cycle = Cycle.objects.filter(device_id=device_id).order_by('-id').first()
#             if latest_cycle:
#                 try:
#                     latest_remaining = float(latest_cycle.remaining)
#                 except Exception:
#                     latest_remaining = None
#                 if latest_remaining == 1.0 and weight_value < 5:
#                     print(f"⛔ MQTT reject: device {device_id} trying to publish weight_initial < 5 when remaining is 1.")
#                     return

#             # ✅ Now safely initialize or get device state
#             device = device_data.setdefault(device_id, {
#                 'weight_initial': None,
#                 'weight_final': None,
#                 'allow_new_weight': True,
#             })

#             current_cycle = device_cycle_tracker.get(device_id, 1)

            # if not device['allow_new_weight'] and weight_value < 5:
            #     print(f"⛔ Skipped: {device_id} sent weight_initial < 5 after final weight 1.0")
            #     return

            # # Start a new cycle if weight_initial changed
            # if device['weight_initial'] is None or weight_value != float(device['weight_initial']):
            #     device_cycle_tracker[device_id] = current_cycle + 1
            #     current_cycle = device_cycle_tracker[device_id]
            #     print(f"🔄 New cycle {current_cycle} started for {device_id}")

#             device['weight_initial'] = weight_value
#             device['weight_final'] = None
#             device['allow_new_weight'] = True

#             MQTTMessage.objects.create(
#                 device_id=device_id,
#                 topic=msg.topic,
#                 weight_intial=str(weight_value),
#                 weight_final=None,
#                 cycle_number=current_cycle,
#                 timestamp=now()
#             )

#             print(f"📥 Device: {device_id} | weight_initial: {weight_value} | Cycle: {current_cycle}")
#             print(f"✅ Saved to DB: {device_id} | weight_initial={weight_value} | cycle={current_cycle}")

#     except Exception as e:
#         print(f"❌ Error in on_message: {e}")


# def publish_message(client, device_id, weight_initial):
#     topic = f"feeder/{device_id}/weight_initial"
#     payload = str(weight_initial)
#     result = client.publish(topic, payload)
#     status = result[0]
#     if status == 0:
#         print(f"✅ Published `{payload}` to `{topic}`")
#     else:
#         print(f"❌ Failed to publish to topic {topic}")


# def mqtt_connect():
#     client = mqtt.Client()
#     client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
#     client.on_connect = on_connect
#     client.on_message = on_message

#     try:
#         client.connect(MQTT_BROKER, MQTT_PORT, 60)
#         client.loop_start()

#         while True:
#             cmd = input("📤 Type 'send', 'cycle', or 'exit': ").strip().lower()
#             if cmd == 'send':
#                 device_id = input("🔧 Enter device_id: ").strip()
#                 weight_initial = input("⚖️  Enter weight_initial: ").strip()
#                 try:
#                     float(weight_initial)
#                     publish_message(client, device_id, weight_initial)
#                 except ValueError:
#                     print("❌ Invalid weight_initial. Must be a number.")
#             elif cmd == 'cycle':
#                 device_id = input("🔧 Enter device_id: ").strip()
#                 cyclecount = input("🔁 Enter cyclecount: ").strip()
#                 try:
#                     float(cyclecount)
#                     frontend_cycle_input(device_id, cyclecount)
#                 except ValueError:
#                     print("❌ Invalid cyclecount. Must be a number.")
#             elif cmd == 'exit':
#                 print("⛔ Stopping client...")
#                 break
#             else:
#                 print("❓ Unknown command. Use 'send', 'cycle', or 'exit'.")

#         client.loop_stop()
#         client.disconnect()

#     except KeyboardInterrupt:
#         print("⛔ Interrupted.")
#         client.loop_stop()
#         client.disconnect()
#     except Exception as e:
#         print(f"❌ Connection error: {e}")


# if __name__ == "__main__":
#     mqtt_connect()






# # new code modification

# # import os
# # import django
# # import paho.mqtt.client as mqtt
# # from django.utils.timezone import now

# # # Set up Django environment
# # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pilot_feedtray.settings")
# # django.setup()

# # from app1.models import MQTTMessage

# # # MQTT broker credentials and topics
# # MQTT_BROKER = 'mqttbroker.bc-pl.com'
# # MQTT_PORT = 1883
# # MQTT_USER = 'mqttuser'
# # MQTT_PASSWORD = 'Bfl@2025'

# # MQTT_TOPICS = [
# #     'feeder/fdtryA00/weight_initial',
# #     'feeder/fdtryA00/weight_final',
# #     'feeder/fdtryA00/cycle_status',
# # ]

# # # In-memory device trackers
# # device_cycle_tracker = {}  # Tracks current cycle per device
# # device_data = {}           # Stores device state

# # def on_connect(client, userdata, flags, rc):
# #     if rc == 0:
# #         print("✅ Connected to MQTT broker.")
# #         for topic in MQTT_TOPICS:
# #             client.subscribe(topic)
# #             print(f"📡 Subscribed to: {topic}")
# #     else:
# #         print(f"❌ MQTT connection failed with code {rc}")

# # def on_message(client, userdata, msg):
# #     try:
# #         payload = msg.payload.decode('utf-8').strip()
# #         topic_parts = msg.topic.split('/')
# #         device_id = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
# #         topic_name = topic_parts[2] if len(topic_parts) > 2 else 'unknown'
# #         timestamp = now()

# #         # Get current cycle number
# #         current_cycle = device_cycle_tracker.get(device_id, 0)

# #         # Set up initial state for device
# #         device = device_data.setdefault(device_id, {
# #             'weight_initial': None,
# #             'weight_final': None,
# #             'allow_new_weight': True,
# #         })

# #         # Handle weight_initial topic
# #         if topic_name == 'weight_initial':
# #             try:
# #                 weight_value = float(payload)
# #             except ValueError:
# #                 print(f"❌ Invalid weight_initial: {payload}")
# #                 return

            # if not device['allow_new_weight'] and weight_value < 5:
            #     print(f"⛔ Rejected: {device_id} sent weight_initial < 5 after final weight 1.0")
            #     return

            # # Modify this condition to also increment cycle if weight_initial == 1.0
            # if (
            #     device['weight_initial'] is None or
            #     weight_value != float(device['weight_initial']) or
            #     weight_value == 1.0
            # ):
            #     current_cycle += 1
            #     device_cycle_tracker[device_id] = current_cycle
            #     print(f"🔄 New cycle {current_cycle} started for {device_id}")

# #             device['weight_initial'] = weight_value
# #             device['weight_final'] = None
# #             device['allow_new_weight'] = True

# #             MQTTMessage.objects.create(
# #                 device_id=device_id,
# #                 topic=msg.topic,
# #                 weight_initial=str(weight_value),
# #                 weight_final=None,
# #                 cycle_number=current_cycle,
# #                 timestamp=timestamp,
# #             )

# #             print(f"📥 {device_id} | weight_initial: {weight_value} | cycle: {current_cycle}")

# #         # Handle weight_final topic
# #         elif topic_name == 'weight_final':
# #             try:
# #                 weight_value = float(payload)
# #             except ValueError:
# #                 print(f"❌ Invalid weight_final: {payload}")
# #                 return

# #             device['weight_final'] = weight_value

# #             MQTTMessage.objects.create(
# #                 device_id=device_id,
# #                 topic=msg.topic,
# #                 weight_initial=str(device['weight_initial']),
# #                 weight_final=str(weight_value),
# #                 cycle_number=current_cycle,
# #                 timestamp=timestamp,
# #             )

# #             if weight_value == 1.0:
# #                 device['allow_new_weight'] = False
# #                 print(f"✅ Cycle {current_cycle} marked as complete for {device_id}")

# #             print(f"📥 {device_id} | weight_final: {weight_value} | cycle: {current_cycle}")

        # # Handle cycle_status topic
        # elif topic_name == 'cycle_status':
        #     # Remove quotes and normalize
        #     cleaned_payload = payload.strip().lower().replace('"', '').replace("'", "")

        #     if cleaned_payload == 'status: completed':
        #         MQTTMessage.objects.create(
        #             device_id=device_id,
        #             topic=msg.topic,
        #             cycle_status='status: completed',
        #             cycle_number=current_cycle,
        #             timestamp=timestamp,
        #         )
        #         print(f"📥 {device_id} | cycle_status: {'status: completed'} ,at {timestamp}")
        #     else:
        #         print(f"ℹ️ Unknown cycle_status: {payload}")


# #     except Exception as e:
# #         print(f"❌ Error in on_message: {e}")


# # def mqtt_connect():
# #     client = mqtt.Client()
# #     client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
# #     client.on_connect = on_connect
# #     client.on_message = on_message

# #     try:
# #         client.connect(MQTT_BROKER, MQTT_PORT, 60)
# #         client.loop_start()

# #         while True:
# #             cmd = input("📤 Type 'exit' to stop: ").strip().lower()
# #             if cmd == 'exit':
# #                 print("⛔ Stopping client...")
# #                 break
# #             else:
# #                 print("❓ Unknown command. Type 'exit' to quit.")

# #         client.loop_stop()
# #         client.disconnect()

# #     except KeyboardInterrupt:
# #         print("⛔ Interrupted.")
# #         client.loop_stop()
# #         client.disconnect()
# #     except Exception as e:
# #         print(f"❌ Connection error: {e}")

# # if __name__ == "__main__":
# #     mqtt_connect()











# ###date - 06/06/2025
# import os
# import django
# import paho.mqtt.client as mqtt
# from django.utils.timezone import now

# # Uncomment and configure if running standalone script outside manage.py
# # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pilot_feedtray.settings")
# # django.setup()

# from app1.models import MQTTMessage  # Import your Django model

# MQTT_BROKER = 'mqttbroker.bc-pl.com'
# MQTT_PORT = 1883
# MQTT_USER = 'mqttuser'
# MQTT_PASSWORD = 'Bfl@2025'

# MQTT_TOPICS = [
#     'feeder/fdtryA00/weight_initial',
#     'feeder/fdtryA00/weight_final',
#     'feeder/fdtryA00/cycle_status',
# ]

# device_cycle_tracker = {}  # Tracks current cycle number per device
# device_data = {}           # Holds per-device current state


# def frontend_cycle_input(device_id, cyclecount):
#     device = device_data.get(device_id)
#     if not device or device['weight_initial'] is None:
#         print(f"❌ No initial weight available for device {device_id}, cannot process cycle input.")
#         return

#     try:
#         weight_initial = float(device['weight_initial'])
#         cyclecount_float = float(cyclecount)
#     except ValueError:
#         print(f"❌ Invalid cyclecount or weight_initial values for device {device_id}")
#         return

#     weight_final = weight_initial - cyclecount_float
#     timestamp = now()
#     current_cycle = device_cycle_tracker.get(device_id,0)

#     MQTTMessage.objects.create(
#         device_id=device_id,
#         topic='cyclecount',
#         weight_initial=str(weight_initial),
#         weight_final=str(weight_final),
#         cyclecount=str(cyclecount_float),
#         cycle_number=current_cycle,
#         timestamp=timestamp,
#     )

#     print(f"✅ Saved cycle data | Device: {device_id} | Cycle: {current_cycle} | Initial: {weight_initial} | Final: {weight_final} | Count: {cyclecount_float}")

#     device['weight_final'] = weight_final
#     if weight_final == 1.0:
#         device['allow_new_weight'] = False
#         print(f"⚠️ Device {device_id}: Final weight reached 1.0. No further weight_initial < 5 will be processed.")


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
#         payload = msg.payload.decode('utf-8').strip()
#         topic_parts = msg.topic.split('/')
#         device_id = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
#         topic_name = topic_parts[2] if len(topic_parts) > 2 else 'unknown'
#         timestamp = now()

#         # Initialize or get device state
#         device = device_data.setdefault(device_id, {
#             'weight_initial': None,
#             'weight_final': None,
#             'allow_new_weight': True,
#         })

#         current_cycle = device_cycle_tracker.get(device_id, 0)

#         if topic_name == 'weight_initial':
#             try:
#                 weight_value = float(payload)
#             except ValueError:
#                 print(f"❌ Invalid weight value: {payload}")
#                 return

#             # Skip low values if not allowed
#             if not device['allow_new_weight'] and weight_value < 5:
#                 print(f"⛔ Skipped: {device_id} sent weight_initial < 5 after final weight 1.0")
#                 return

#             # Always increment cycle, even for same weight_initial
#             current_cycle += 1
#             device_cycle_tracker[device_id] = current_cycle
#             print(f"🔄 New cycle {current_cycle} started for {device_id}")

#             device['weight_initial'] = weight_value
#             device['weight_final'] = None

#             MQTTMessage.objects.create(
#                 device_id=device_id,
#                 topic=msg.topic,
#                 weight_initial=str(weight_value),
#                 weight_final=None,
#                 cycle_number=current_cycle,
#                 timestamp=timestamp
#             )

#             print(f"📥 Device: {device_id} | weight_initial: {weight_value} | Cycle: {current_cycle}")
#             print(f"✅ Saved to DB: {device_id} | weight_initial={weight_value} | cycle={current_cycle}")

#         elif topic_name == 'weight_final':
#             try:
#                 weight_value = float(payload)
#             except ValueError:
#                 print(f"❌ Invalid weight value: {payload}")
#                 return

#             # Start new cycle when weight_final is 1.0
#             if weight_value == 1.0:
#                 current_cycle += 1
#                 device_cycle_tracker[device_id] = current_cycle
#                 print(f"🔄 New cycle {current_cycle} started for {device_id}")
#                 device['allow_new_weight'] = False  # Prevent new weight_initial until status: completed

#             device['weight_final'] = weight_value

#             MQTTMessage.objects.create(
#                 device_id=device_id,
#                 topic=msg.topic,
#                 weight_initial=None,
#                 weight_final=str(weight_value),
#                 cycle_number=current_cycle,
#                 timestamp=timestamp
#             )

#             print(f"📥 Device: {device_id} | weight_final: {weight_value} | Cycle: {current_cycle}")
#             print(f"✅ Saved to DB: {device_id} | weight_final={weight_value} | cycle={current_cycle}")

#         elif topic_name == 'cycle_status':
#             # Normalize payload
#             cleaned_payload = payload.strip().lower().replace('"', '').replace("'", "")
#             current_cycle = device_cycle_tracker.get(device_id, 0)

#             if cleaned_payload == 'status: completed':
#                 device = device_data.setdefault(device_id, {
#                     'weight_initial': None,
#                     'weight_final': None,
#                     'allow_new_weight': True,
#                 })
#                 device['allow_new_weight'] = True  # ✅ Allow new weight_initial
#                 MQTTMessage.objects.create(
#                     device_id=device_id,
#                     topic=msg.topic,
#                     cycle_status='status: completed',
#                     cycle_number=current_cycle,
#                     timestamp=timestamp,
#                 )
#                 print(f"📥 {device_id} | cycle_status: status: completed ,at {timestamp}")
#             else:
#                 print(f"ℹ️ Unknown cycle_status: {payload}")

#     except Exception as e:
#         print(f"❌ Error in on_message: {e}")







# def publish_message(client, device_id, weight_initial):
#     topic = f"feeder/{device_id}/weight_initial"
#     payload = str(weight_initial)
#     result = client.publish(topic, payload)
#     status = result[0]
#     if status == 0:
#         print(f"✅ Published `{payload}` to `{topic}`")
#     else:
#         print(f"❌ Failed to publish to topic {topic}")


# def mqtt_connect():
#     client = mqtt.Client()
#     client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
#     client.on_connect = on_connect
#     client.on_message = on_message

#     try:
#         client.connect(MQTT_BROKER, MQTT_PORT, 60)
#         client.loop_start()

#         while True:
#             cmd = input("📤 Type 'send', 'cycle', or 'exit': ").strip().lower()
#             if cmd == 'send':
#                 device_id = input("🔧 Enter device_id: ").strip()
#                 weight_initial = input("⚖️ Enter weight_initial: ").strip()
#                 try:
#                     float(weight_initial)
#                     publish_message(client, device_id, weight_initial)
#                 except ValueError:
#                     print("❌ Invalid weight_initial. Must be a number.")
#             elif cmd == 'cycle':
#                 device_id = input("🔧 Enter device_id: ").strip()
#                 cyclecount = input("🔁 Enter cyclecount: ").strip()
#                 try:
#                     float(cyclecount)
#                     frontend_cycle_input(device_id, cyclecount)
#                 except ValueError:
#                     print("❌ Invalid cyclecount. Must be a number.")
#             elif cmd == 'exit':
#                 print("⛔ Stopping client...")
#                 break
#             else:
#                 print("❓ Unknown command. Use 'send', 'cycle', or 'exit'.")

#         client.loop_stop()
#         client.disconnect()

#     except KeyboardInterrupt:
#         print("⛔ Interrupted by user.")
#         client.loop_stop()
#         client.disconnect()
#     except Exception as e:
#         print(f"❌ MQTT connection error: {e}")


# if __name__ == "__main__":
#     mqtt_connect()








import os
import django
import paho.mqtt.client as mqtt
from django.utils.timezone import now

# Uncomment and configure if running standalone script outside manage.py
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pilot_feedtray.settings")
# django.setup()

from app1.models import MQTTMessage  # Import your Django model

MQTT_BROKER = 'mqttbroker.bc-pl.com'
MQTT_PORT = 1883
MQTT_USER = 'mqttuser'
MQTT_PASSWORD = 'Bfl@2025'

MQTT_TOPICS = [
    'feeder/fdtryA00/weight_initial',
    'feeder/fdtryA00/weight_final',
    'feeder/fdtryA00/cycle_status',
]

device_cycle_tracker = {}  # Tracks current cycle number per device
device_data = {}           # Holds per-device current state


def frontend_cycle_input(device_id, cyclecount):
    device = device_data.get(device_id)
    if not device or device['weight_initial'] is None:
        print(f"❌ No initial weight available for device {device_id}, cannot process cycle input.")
        return

    try:
        weight_initial = float(device['weight_initial'])
        cyclecount_float = float(cyclecount)
    except ValueError:
        print(f"❌ Invalid cyclecount or weight_initial values for device {device_id}")
        return

    weight_final = weight_initial - cyclecount_float
    timestamp = now()
    current_cycle = device_cycle_tracker.get(device_id,0)

    MQTTMessage.objects.create(
        device_id=device_id,
        topic='cyclecount',
        weight_initial=str(weight_initial),
        weight_final=str(weight_final),
        cyclecount=str(cyclecount_float),
        cycle_number=current_cycle,
        timestamp=timestamp,
    )

    print(f"✅ Saved cycle data | Device: {device_id} | Cycle: {current_cycle} | Initial: {weight_initial} | Final: {weight_final} | Count: {cyclecount_float}")

    device['weight_final'] = weight_final
    if weight_final == 1.0:
        device['allow_new_weight'] = False
        print(f"⚠️ Device {device_id}: Final weight reached 1.0. No further weight_initial < 5 will be processed.")


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
        payload = msg.payload.decode('utf-8').strip()
        topic_parts = msg.topic.split('/')
        device_id = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
        topic_name = topic_parts[2] if len(topic_parts) > 2 else 'unknown'
        timestamp = now()

        # Initialize or get device state
        device = device_data.setdefault(device_id, {
            'weight_initial': None,
            'weight_final': None,
            'allow_new_weight': True,
        })

        current_cycle = device_cycle_tracker.get(device_id, 0)

        if topic_name == 'weight_initial':
            try:
                weight_value = float(payload)
            except ValueError:
                print(f"❌ Invalid weight value: {payload}")
                return

            # Skip low values if not allowed
            if not device['allow_new_weight'] and weight_value < 5:
                print(f"⛔ Skipped: {device_id} sent weight_initial < 5 after final weight 1.0")
                return

            # Always increment cycle, even for same weight_initial
            current_cycle += 1
            device_cycle_tracker[device_id] = current_cycle
            print(f"🔄 New cycle {current_cycle} started for {device_id}")

            device['weight_initial'] = weight_value
            device['weight_final'] = None

            MQTTMessage.objects.create(
                device_id=device_id,
                topic=msg.topic,
                weight_initial=str(weight_value),
                weight_final=None,
                cycle_number=current_cycle,
                timestamp=timestamp
            )

            print(f"📥 Device: {device_id} | weight_initial: {weight_value} | Cycle: {current_cycle}")
            print(f"✅ Saved to DB: {device_id} | weight_initial={weight_value} | cycle={current_cycle}")

        elif topic_name == 'weight_final':
            try:
                weight_value = float(payload)
            except ValueError:
                print(f"❌ Invalid weight value: {payload}")
                return

            # Start new cycle when weight_final is 1.0
            if weight_value == 1.0:
                current_cycle += 1
                device_cycle_tracker[device_id] = current_cycle
                print(f"🔄 New cycle {current_cycle} started for {device_id}")
                device['allow_new_weight'] = False  # Prevent new weight_initial until status: completed

            device['weight_final'] = weight_value

            MQTTMessage.objects.create(
                device_id=device_id,
                topic=msg.topic,
                weight_initial=None,
                weight_final=str(weight_value),
                cycle_number=current_cycle,
                timestamp=timestamp
            )

            print(f"📥 Device: {device_id} | weight_final: {weight_value} | Cycle: {current_cycle}")
            print(f"✅ Saved to DB: {device_id} | weight_final={weight_value} | cycle={current_cycle}")

        elif topic_name == 'cycle_status':
            # Normalize payload
            cleaned_payload = payload.strip().lower().replace('"', '').replace("'", "")
            current_cycle = device_cycle_tracker.get(device_id, 0)

            if cleaned_payload == 'status: completed':
                device = device_data.setdefault(device_id, {
                    'weight_initial': None,
                    'weight_final': None,
                    'allow_new_weight': True,
                })
                device['allow_new_weight'] = True  # ✅ Allow new weight_initial
                MQTTMessage.objects.create(
                    device_id=device_id,
                    topic=msg.topic,
                    cycle_status='status: completed',
                    cycle_number=current_cycle,
                    timestamp=timestamp,
                )
                print(f"📥 {device_id} | cycle_status: status: completed ,at {timestamp}")
            else:
                print(f"ℹ️ Unknown cycle_status: {payload}")

    except Exception as e:
        print(f"❌ Error in on_message: {e}")




def publish_message(client, device_id, weight_initial):
    topic = f"feeder/{device_id}/weight_initial"
    payload = str(weight_initial)
    result = client.publish(topic, payload)
    status = result[0]
    if status == 0:
        print(f"✅ Published `{payload}` to `{topic}`")
    else:
        print(f"❌ Failed to publish to topic {topic}")


def mqtt_connect():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        while True:
            cmd = input("📤 Type 'send', 'cycle', or 'exit': ").strip().lower()
            if cmd == 'send':
                device_id = input("🔧 Enter device_id: ").strip()
                weight_initial = input("⚖️ Enter weight_initial: ").strip()
                try:
                    float(weight_initial)
                    publish_message(client, device_id, weight_initial)
                except ValueError:
                    print("❌ Invalid weight_initial. Must be a number.")
            elif cmd == 'cycle':
                device_id = input("🔧 Enter device_id: ").strip()
                cyclecount = input("🔁 Enter cyclecount: ").strip()
                try:
                    float(cyclecount)
                    frontend_cycle_input(device_id, cyclecount)
                except ValueError:
                    print("❌ Invalid cyclecount. Must be a number.")
            elif cmd == 'exit':
                print("⛔ Stopping client...")
                break
            else:
                print("❓ Unknown command. Use 'send', 'cycle', or 'exit'.")

        client.loop_stop()
        client.disconnect()

    except KeyboardInterrupt:
        print("⛔ Interrupted by user.")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"❌ MQTT connection error: {e}")


# --- Added function as requested ---

def on_new_mqtt_message(payload):
    """
    payload is a dict with at least:
    {
      'device_id': 'fdtryA00',
      'weight_initial': '200.0',    # string or float
      'cycle_number': '2',          # string or int
      'topic': 'some/topic/weight_initial'
    }
    """
    device_id = payload.get('device_id')
    if not device_id:
        return  # or log error

    try:
        weight_initial = float(payload.get('weight_initial'))
        cycle_number = int(payload.get('cycle_number'))
    except (TypeError, ValueError):
        return  # invalid data; log error

    # Get last MQTTMessage for device
    last_msg = MQTTMessage.objects.filter(device_id=device_id).order_by('-timestamp', '-id').first()

    # If no previous message, or previous cycle ended (weight_final == 1), treat this as new cycle start
    if last_msg is None or last_msg.weight_final == 1:
        # Save new cycle start message
        MQTTMessage.objects.create(
            device_id=device_id,
            weight_initial=weight_initial,
            weight_final=None,
            cycle_number=cycle_number,
            timestamp=now(),
            topic=payload.get('topic', '')
        )
        print(f"🔄 New cycle {cycle_number} started for {device_id} with weight_initial {weight_initial}")
    else:
        # If still in the middle of a cycle, just save the message normally
        MQTTMessage.objects.create(
            device_id=device_id,
            weight_initial=weight_initial,
            weight_final=None,
            cycle_number=cycle_number,
            timestamp=now(),
            topic=payload.get('topic', '')
        )


if __name__ == "__main__":
    mqtt_connect()
