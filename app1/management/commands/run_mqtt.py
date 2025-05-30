from django.core.management.base import BaseCommand
from app1.paho_mqtt import mqtt_connect

class Command(BaseCommand):
    help = 'Start MQTT subscriber to save messages to DB'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting MQTT subscription...")
        mqtt_connect()
