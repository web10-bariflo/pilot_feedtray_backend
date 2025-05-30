from django.http import JsonResponse
from app1.models import MQTTMessage
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.http import JsonResponse
from app1.models import MQTTMessage
from django.core.serializers import serialize
from django.db.models import Count
from .models import MQTTMessage
from django.http import JsonResponse
from collections import defaultdict


# def ordered_mqtt_data(request):
#     data = list(MQTTMessage.objects.all().order_by('id').values(
#         'id', 'device_id', 'topic', 'payload', 'timestamp'
#     ))
#     return JsonResponse(data, safe=False)



@csrf_exempt
def get_deviceid_data(request, device_id):
    if request.method == 'GET':
        messages = MQTTMessage.objects.filter(device_id=device_id).order_by('-timestamp')
        data = [
            {
                "device_id": data.device_id,
                "cycle_number": data.cycle_number,
                "topic": data.topic,
                "payload": data.payload,
                "timestamp": data.timestamp.isoformat()
            }
            for data in messages
        ]
        return JsonResponse(data, safe=False)
    return JsonResponse({"error": "Method not allowed"}, status=405)



@csrf_exempt
def get_mqttdata(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        messages = MQTTMessage.objects.all().order_by('device_id', 'cycle_number', 'timestamp')

        data = []

        # We'll prepare a quick lookup for weight_initial and weight_final per device+cycle
        # To display those in the rows accordingly
        weight_initial_map = {}
        weight_final_map = {}

        for msg in messages:
            key = (msg.device_id, msg.cycle_number)
            if msg.topic == 'weight_initial':
                weight_initial_map[key] = msg.payload
            elif msg.topic == 'weight_final':
                weight_final_map[key] = msg.payload

        # Now build the final list
        for msg in messages:
            key = (msg.device_id, msg.cycle_number)
            data.append({
                'device_id': msg.device_id,
                'topic': msg.topic,
                'weight_initial': weight_initial_map.get(key, '') if msg.topic != 'weight_initial' else msg.payload,
                'weight_final': weight_final_map.get(key, '') if msg.topic != 'weight_final' else msg.payload,
                'cycle_count': msg.cycle_number,
                'timestamp': msg.timestamp.strftime("%b %d, %Y, %I:%M %p"),
            })

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    




@csrf_exempt
def cyclecount_api(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cyclecount = data.get('cyclecount')

            if not cyclecount:
                return JsonResponse({
                    'success': False,
                    'message': 'cyclecount is required.'
                }, status=400)

            message = MQTTMessage.objects.create(
                device_id='',
                topic='cycle_count',
                payload=cyclecount
            )

            return JsonResponse({
                'success': True,
                'message': 'Cycle count posted successfully.',
                'data': {
                    # 'id': message.id,
                    'cyclecount': message.payload,
                    'timestamp': message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON.'
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while saving the cycle count.',
                'error': str(e)
            }, status=500)



    elif request.method == 'GET':
        try:
            messages = MQTTMessage.objects.filter(topic='cycle_count').order_by('-timestamp')

            if not messages.exists():
                print("No cycle count data found.")
                return JsonResponse([], safe=False, status=200)

            data = [
                {
                    'cyclecount': msg.payload,
                    'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
                for msg in messages
            ]

            return JsonResponse(data, safe=False, status=200)

        except Exception as e:
            print(f"Error fetching cycle count: {e}")
            return JsonResponse([], safe=False, status=500)

    
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid HTTP method. Use GET or POST.'
        }, status=405)
    


