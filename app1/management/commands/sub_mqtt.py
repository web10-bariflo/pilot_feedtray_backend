from django.core.management.base import BaseCommand
from app1.subscribe import start_mqtt_subscriber  # Make sure this is correct

class Command(BaseCommand):
    help = 'Start MQTT subscriber to save messages to DB'

    def handle(self, *args, **kwargs):
        self.stdout.write("✅ Starting MQTT subscription listener...")
        start_mqtt_subscriber()
