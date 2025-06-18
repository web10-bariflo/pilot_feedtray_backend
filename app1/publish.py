import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = 'mqttbroker.bc-pl.com'
MQTT_PORT = 1883
MQTT_TOPIC = 'feeder/fdtryA00/cycle_status'
MQTT_USER = 'mqttuser'
MQTT_PASSWORD = 'Bfl@2025'

# Create client and set username/password
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

# Connect and publish message
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    message = 'all cycle completed'
    client.publish(MQTT_TOPIC, message)
    print(f"[✓] Published '{message}' to topic '{MQTT_TOPIC}'")
    client.disconnect()
except Exception as e:
    print("[!] Failed to publish message:", e)
