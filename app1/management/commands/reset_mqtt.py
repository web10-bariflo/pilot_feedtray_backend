# from django.core.management.base import BaseCommand
# from app1.models import MQTTMessage
# from django.db import connection

# class Command(BaseCommand):
#     help = "Delete all MQTT data and reset ID counter to 1."

#     def handle(self, *args, **kwargs):
#         self.stdout.write("Deleting all MQTTMessage records...")
#         MQTTMessage.objects.all().delete()

#         with connection.cursor() as cursor:
#             db_engine = connection.settings_dict['ENGINE']
#             if 'postgresql' in db_engine:
#                 cursor.execute("ALTER SEQUENCE app1_mqttmessage_id_seq RESTART WITH 1")
#             elif 'sqlite3' in db_engine:
#                 cursor.execute("DELETE FROM sqlite_sequence WHERE name='app1_mqttmessage'")
#             else:
#                 self.stdout.write(self.style.WARNING("Manual sequence reset might be needed for your DB engine."))

#         self.stdout.write(self.style.SUCCESS("All records deleted and ID reset to 1."))




    
