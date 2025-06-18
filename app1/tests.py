from django.test import TestCase

# Create your tests here.

# # ###date - 06/06/2025
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





#################################################################################################

# import os
# import django
# import paho.mqtt.client as mqtt
# from django.utils.timezone import now

# # Django setup
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pilot_feedtray.settings")
# django.setup()

# from app1.models import MQTTMessage

# MQTT_BROKER = 'mqttbroker.bc-pl.com'
# MQTT_PORT = 1883
# MQTT_USER = 'mqttuser'
# MQTT_PASSWORD = 'Bfl@2025'

# MQTT_TOPICS = [
#     'feeder/fdtryA00/weight_initial',
#     'feeder/fdtryA00/weight_final',
#     'feeder/fdtryA00/cycle_status',
# ]

# # MQTT client instance
# client = mqtt.Client()


# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("✅ Connected to MQTT broker.")
#         for topic in MQTT_TOPICS:
#             client.subscribe(topic)
#             print(f"📡 Subscribed to: {topic}")
#     else:
#         print(f"❌ MQTT connection failed with code {rc}")


# def publish_rejection_message(device_id, reason):
#     topic = f"feeder/{device_id}/rejection"
#     client.publish(topic, reason)
#     print(f"🚫 Rejection sent: {reason} → {topic}")


# def on_message(client, userdata, msg):
#     try:
#         payload = msg.payload.decode('utf-8').strip()
#         topic_parts = msg.topic.split('/')
#         device_id = topic_parts[1] if len(topic_parts) > 1 else 'unknown'
#         topic_name = topic_parts[2] if len(topic_parts) > 2 else 'unknown'
#         timestamp = now()

#         if topic_name == 'weight_final':
#             try:
#                 final_val = float(payload)
#             except ValueError:
#                 print(f"❌ Invalid weight_final: {payload}")
#                 return

#             MQTTMessage.objects.create(
#                 device_id=device_id,
#                 topic=msg.topic,
#                 weight_initial=None,
#                 weight_final=str(final_val),
#                 cycle_number=None,
#                 timestamp=timestamp,
#             )
#             print(f"✅ SAVED: {device_id} | weight_final={final_val}")

#         elif topic_name == 'weight_initial':
#             try:
#                 init_val = float(payload)
#             except ValueError:
#                 print(f"❌ Invalid weight_initial: {payload}")
#                 return

#             # Check if last weight_final was 1 for this device
#             last_final_1 = MQTTMessage.objects.filter(
#                 device_id=device_id,
#                 weight_final="1.0"
#             ).order_by('-timestamp').first()

#             if last_final_1 and init_val < 5:
#                 msg = "❌ You cannot publish weight_initial < 5 when weight_final is 1"
#                 publish_rejection_message(device_id, msg)
#                 print(f"⛔ BLOCKED: weight_initial={init_val} for {device_id} rejected due to previous weight_final=1")
#                 return

#             # Save valid weight_initial
#             MQTTMessage.objects.create(
#                 device_id=device_id,
#                 topic=msg.topic,
#                 weight_initial=str(init_val),
#                 weight_final=None,
#                 cycle_number=None,
#                 timestamp=timestamp,
#             )
#             print(f"✅ SAVED: {device_id} | weight_initial={init_val}")

#         elif topic_name == 'cycle_status':
#             cleaned = payload.lower().strip()
#             if cleaned == "status: completed":
#                 MQTTMessage.objects.create(
#                     device_id=device_id,
#                     topic=msg.topic,
#                     cycle_status=cleaned,
#                     cycle_number=None,
#                     timestamp=timestamp
#                 )
#                 print(f"🔁 COMPLETED: {device_id} | Cycle marked as completed")

#     except Exception as e:
#         print(f"❌ Error in on_message: {e}")


# def mqtt_connect():
#     client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
#     client.on_connect = on_connect
#     client.on_message = on_message

#     try:
#         client.connect(MQTT_BROKER, MQTT_PORT, 60)
#         client.loop_forever()
#     except KeyboardInterrupt:
#         print("🛑 Stopped by user")
#     except Exception as e:
#         print(f"❌ MQTT Connection Error: {e}")


# if __name__ == "__main__":
#     print("Starting MQTT subscription...")
#     mqtt_connect()