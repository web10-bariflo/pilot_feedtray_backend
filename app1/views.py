# from django.http import JsonResponse
# from app1.models import MQTTMessage
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# import json
# from django.http import JsonResponse
# from app1.models import MQTTMessage
# from django.core.serializers import serialize
# from django.db.models import Count
# from .models import MQTTMessage
# from django.http import JsonResponse
# from collections import defaultdict


# # def ordered_mqtt_data(request):
# #     data = list(MQTTMessage.objects.all().order_by('id').values(
# #         'id', 'device_id', 'topic', 'payload', 'timestamp'
# #     ))
# #     return JsonResponse(data, safe=False)



# @csrf_exempt
# def get_deviceid_data(request, device_id):
#     if request.method == 'GET':
#         messages = MQTTMessage.objects.filter(device_id=device_id).order_by('-timestamp')
#         data = [
#             {
#                 "device_id": data.device_id,
#                 "cycle_number": data.cycle_number,
#                 "topic": data.topic,
#                 "payload": data.payload,
#                 "timestamp": data.timestamp.isoformat()
#             }
#             for data in messages
#         ]
#         return JsonResponse(data, safe=False)
#     return JsonResponse({"error": "Method not allowed"}, status=405)



# @csrf_exempt
# def get_mqttdata(request):
#     if request.method != 'GET':
#         return JsonResponse({'error': 'Method not allowed'}, status=405)

#     try:
#         messages = MQTTMessage.objects.all().order_by('device_id', 'cycle_number', 'timestamp')

#         data = []

#         # We'll prepare a quick lookup for weight_initial and weight_final per device+cycle
#         # To display those in the rows accordingly
#         weight_initial_map = {}
#         weight_final_map = {}

#         for msg in messages:
#             key = (msg.device_id, msg.cycle_number)
#             if msg.topic == 'weight_initial':
#                 weight_initial_map[key] = msg.payload
#             elif msg.topic == 'weight_final':
#                 weight_final_map[key] = msg.payload

#         # Now build the final list
#         for msg in messages:
#             key = (msg.device_id, msg.cycle_number)
#             data.append({
#                 'device_id': msg.device_id,
#                 'topic': msg.topic,
#                 'weight_initial': weight_initial_map.get(key, '') if msg.topic != 'weight_initial' else msg.payload,
#                 'weight_final': weight_final_map.get(key, '') if msg.topic != 'weight_final' else msg.payload,
#                 'cycle_count': msg.cycle_number,
#                 'timestamp': msg.timestamp.strftime("%b %d, %Y, %I:%M %p"),
#             })

#         return JsonResponse(data, safe=False)

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
    




# @csrf_exempt
# def cyclecount_api(request):

#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             cyclecount = data.get('cyclecount')

#             if not cyclecount:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'cyclecount is required.'
#                 }, status=400)

#             message = MQTTMessage.objects.create(
#                 device_id='',
#                 topic='cycle_count',
#                 payload=cyclecount
#             )

#             return JsonResponse({
#                 'success': True,
#                 'message': 'Cycle count posted successfully.',
#                 'data': {
#                     # 'id': message.id,
#                     'cyclecount': message.payload,
#                     'timestamp': message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
#                 }
#             }, status=201)

#         except json.JSONDecodeError:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'Invalid JSON.'
#             }, status=400)

#         except Exception as e:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'An error occurred while saving the cycle count.',
#                 'error': str(e)
#             }, status=500)



#     elif request.method == 'GET':
#         try:
#             messages = MQTTMessage.objects.filter(topic='cycle_count').order_by('-timestamp')

#             if not messages.exists():
#                 print("No cycle count data found.")
#                 return JsonResponse([], safe=False, status=200)

#             data = [
#                 {
#                     'cyclecount': msg.payload,
#                     'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
#                 }
#                 for msg in messages
#             ]

#             return JsonResponse(data, safe=False, status=200)

#         except Exception as e:
#             print(f"Error fetching cycle count: {e}")
#             return JsonResponse([], safe=False, status=500)

    
#     else:
#         return JsonResponse({
#             'success': False,
#             'message': 'Invalid HTTP method. Use GET or POST.'
#         }, status=405)
    

from django.http import JsonResponse
from django.views import View
from django.utils.timezone import now
from app1.models import MQTTMessage

device_cycle_tracker = {}

class SaveMQTTMessageView(View):
    def post(self, request):
        try:
            data = request.POST
            device_id = data.get('device_id')
            topic = data.get('topic')
            weight_initial = float(data.get('weight_initial'))

            if not device_id or not topic:
                return JsonResponse({"error": "Missing fields."}, status=400)

            latest = MQTTMessage.objects.filter(device_id=device_id).order_by('-timestamp').first()

            # Prevent weight_initial < 5 after final weight 1.0
            if weight_initial < 5 and latest and latest.weight_final == "1.0":
                return JsonResponse({
                    "error": "Rejected: weight_initial < 5 after final weight was 1.0"
                }, status=400)

            current_cycle = device_cycle_tracker.get(device_id, 1)
            if latest and float(latest.weight_intial) != weight_initial:
                current_cycle += 1
            device_cycle_tracker[device_id] = current_cycle

            mqtt_message = MQTTMessage.objects.create(
                device_id=device_id,
                topic=topic,
                weight_intial=str(weight_initial),
                weight_final=None,
                timestamp=now(),
                cycle_number=current_cycle
            )

            return JsonResponse({
                "message": "MQTT data saved",
                "device_id": mqtt_message.device_id,
                "weight_initial": mqtt_message.weight_intial,
                "cycle_number": mqtt_message.cycle_number
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        



import json
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from app1.models import Cycle, MQTTMessage


@method_decorator(csrf_exempt, name='dispatch')
class SaveCycleCountView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            cyclecount = data.get('cyclecount')

            if not device_id:
                return JsonResponse({"error": "Missing device_id."}, status=400)
            if cyclecount is None:
                return JsonResponse({"error": "Missing cyclecount."}, status=400)

            try:
                cyclecount = float(cyclecount)
            except ValueError:
                return JsonResponse({"error": "Invalid cyclecount. Must be a number."}, status=400)

            # Step 1: Find latest weight_initial published by MQTT
            latest_weight_initial_entry = MQTTMessage.objects.filter(
                device_id=device_id,
                weight_intial__isnull=False
            ).order_by('-timestamp').first()

            if not latest_weight_initial_entry:
                return JsonResponse({"error": "No weight_initial found for this device."}, status=404)

            weight_initial = float(latest_weight_initial_entry.weight_intial)

            # Step 2: Now find the latest weight_final corresponding to that weight_initial
            latest_cycle_entry = MQTTMessage.objects.filter(
                device_id=device_id,
                weight_intial=weight_initial,
                weight_final__isnull=False
            ).order_by('-timestamp').first()

            if latest_cycle_entry:
                # Use latest weight_final as new weight_initial
                new_weight_initial = float(latest_cycle_entry.weight_final)
                cycle_number = latest_cycle_entry.cycle_number + 1
            else:
                # No previous cycle done on this weight_initial
                new_weight_initial = weight_initial
                cycle_number = latest_weight_initial_entry.cycle_number + 1 if latest_weight_initial_entry.cycle_number else 1

            if cyclecount >= new_weight_initial:
                return JsonResponse({
                    "error": f"Cycle count ({cyclecount}) must be less than available weight ({new_weight_initial})."
                }, status=400)

            weight_final = new_weight_initial - cyclecount

            # Save new MQTTMessage
            MQTTMessage.objects.create(
                device_id=device_id,
                weight_intial=new_weight_initial,
                weight_final=weight_final,
                cycle_number=cycle_number,
                timestamp=now(),
                topic=latest_weight_initial_entry.topic
            )

            # Save new Cycle
            Cycle.objects.create(
                device_id=device_id,
                cyclecount=str(cyclecount),
                remaining=str(weight_final)
            )

            return JsonResponse({
                "message": "Cycle and MQTTMessage saved.",
                "device_id": device_id,
                "cycle_number": cycle_number,
                "weight_initial": new_weight_initial,
                "cyclecount": cyclecount,
                "weight_final": weight_final
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
