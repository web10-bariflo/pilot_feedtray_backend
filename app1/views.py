# from django.http import JsonResponse
# from django.views import View
# from django.utils.timezone import now
# from app1.models import MQTTMessage

# device_cycle_tracker = {}

# class SaveMQTTMessageView(View):
#     def post(self, request):
#         try:
#             data = request.POST
#             device_id = data.get('device_id')
#             topic = data.get('topic')
#             weight_initial = data.get('weight_initial')
#             cycle_status = data.get('cycle_status')  # Optional

#             if not device_id or not topic:
#                 return JsonResponse({"error": "Missing fields."}, status=400)

#             latest = MQTTMessage.objects.filter(device_id=device_id).order_by('-timestamp').first()

#             # Handle only weight_initial if provided
#             weight_initial_float = float(weight_initial) if weight_initial else None

#             if weight_initial_float is not None:
#                 if weight_initial_float < 5 and latest and latest.weight_final == "1.0":
#                     return JsonResponse({
#                         "error": "Rejected: weight_initial < 5 after final weight was 1.0"
#                     }, status=400)

#                 current_cycle = device_cycle_tracker.get(device_id, 1)
#                 if latest and latest.weight_initial and float(latest.weight_initial) != weight_initial_float:
#                     current_cycle += 1
#                 device_cycle_tracker[device_id] = current_cycle

#                 mqtt_message = MQTTMessage.objects.create(
#                     device_id=device_id,
#                     topic=topic,
#                     weight_initial=str(weight_initial_float),
#                     weight_final=None,
#                     timestamp=now(),
#                     cycle_number=current_cycle
#                 )

#                 return JsonResponse({
#                     "message": "MQTT data saved",
#                     "device_id": mqtt_message.device_id,
#                     "weight_initial": mqtt_message.weight_initial,
#                     "cycle_number": mqtt_message.cycle_number
#                 }, status=201)

#             # Handle cycle_status only
#             elif cycle_status:
#                 cleaned_status = cycle_status.strip().lower().replace('"', '')
#                 if cleaned_status == 'status: completed':
#                     current_cycle = device_cycle_tracker.get(device_id, 1)
#                     mqtt_message = MQTTMessage.objects.create(
#                         device_id=device_id,
#                         topic=topic,
#                         cycle_status='status_completed',
#                         cycle_number=current_cycle,
#                         timestamp=now()
#                     )
#                     return JsonResponse({
#                         "message": "Cycle status saved",
#                         "device_id": device_id,
#                         "cycle_status": 'status: completed',
#                         "cycle_number": current_cycle,
#                         "timestamp": mqtt_message.timestamp
#                     }, status=201)
#                 else:
#                     return JsonResponse({
#                         "message": "Unknown cycle_status value",
#                         "received": cycle_status
#                     }, status=400)

#             else:
#                 return JsonResponse({"error": "No weight_initial or cycle_status provided."}, status=400)

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)

        





import json
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from app1.models import MQTTMessage


@method_decorator(csrf_exempt, name='dispatch')
class SaveMQTTMessageView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            device_id = data.get('device_id')
            topic = data.get('topic')
            weight_initial = data.get('weight_initial')
            weight_final = data.get('weight_final')
            cycle_status = data.get('cycle_status')
            cyclecount = data.get('cyclecount')
            cycle_number = data.get('cycle_number')  # Cycle number from publisher

            # Validate required fields
            if not device_id or not topic:
                return JsonResponse({"error": "Missing device_id or topic"}, status=400)
            if cycle_number is None:
                return JsonResponse({"error": "Missing cycle_number from publisher"}, status=400)
            try:
                cycle_number = int(cycle_number)
            except ValueError:
                return JsonResponse({"error": "Invalid cycle_number format"}, status=400)

            # Handle weight_initial
            if weight_initial is not None:
                weight_initial = float(weight_initial)

                if weight_initial == 1.0:
                    return JsonResponse({
                        "error": "❌ weight_initial is 1.0. Cycle reset detected. Cannot save until new weight_initial > 1.0",
                        "weight_initial": weight_initial
                    }, status=400)

                mqtt_msg = MQTTMessage.objects.create(
                    device_id=device_id,
                    topic=topic,
                    weight_initial=str(weight_initial),
                    weight_final=None,
                    cycle_number=cycle_number,
                    timestamp=now()
                )

                return JsonResponse({
                    "message": "✅ weight_initial saved",
                    "device_id": device_id,
                    "weight_initial": weight_initial,
                    "cycle_number": cycle_number
                }, status=201)

            # Handle weight_final
            if weight_final is not None:
                weight_final = float(weight_final)

                latest_initial = MQTTMessage.objects.filter(
                    device_id=device_id,
                    cycle_number=cycle_number,
                    weight_final__isnull=True
                ).order_by('-timestamp').first()

                mqtt_msg = MQTTMessage.objects.create(
                    device_id=device_id,
                    topic=topic,
                    weight_initial=latest_initial.weight_initial if latest_initial else None,
                    weight_final=str(weight_final),
                    cycle_number=cycle_number,
                    timestamp=now()
                )

                return JsonResponse({
                    "message": "✅ weight_final saved",
                    "device_id": device_id,
                    "weight_final": weight_final,
                    "cycle_number": cycle_number
                }, status=201)

            # Handle cycle_status
            if cycle_status:
                cleaned_status = cycle_status.strip().lower().replace('"', '').replace("'", "")
                if cleaned_status == 'status: completed':
                    mqtt_msg = MQTTMessage.objects.create(
                        device_id=device_id,
                        topic=topic,
                        cycle_status='status_completed',
                        cycle_number=cycle_number,
                        timestamp=now()
                    )
                    return JsonResponse({
                        "message": "✅ cycle_status saved",
                        "device_id": device_id,
                        "cycle_status": 'status_completed',
                        "cycle_number": cycle_number,
                        "timestamp": mqtt_msg.timestamp,
                    }, status=201)
                else:
                    return JsonResponse({
                        "error": f"⚠️ Unknown cycle_status value: {cycle_status}"
                    }, status=400)

            return JsonResponse({"error": "❌ No valid data provided to store."}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)














#new cyclecountimport json
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
            cyclecount = data.get('cyclecount')
            if cyclecount is None:
                return JsonResponse({"error": "Missing cyclecount."}, status=400)
            try:
                cyclecount = float(cyclecount)
            except ValueError:
                return JsonResponse({"error": "Invalid cyclecount. Must be a number."}, status=400)

            # Get latest MQTTMessage entry to infer device_id and current cycle state
            latest_entry = MQTTMessage.objects.order_by('-timestamp', '-id').first()
            if not latest_entry:
                return JsonResponse({"error": "No MQTT data found in DB."}, status=404)

            device_id = latest_entry.device_id
            cycle_number = latest_entry.cycle_number or 1

            # If cycle ended (weight_final == 1), reject cyclecount posts until new cycle starts
            if latest_entry.weight_final == 1:
                return JsonResponse({
                    "error": "Cycle ended (weight_final=1). Please wait for new cycle data from publisher."
                }, status=400)

            # Calculate new weight_final from cyclecount
            weight_initial = float(latest_entry.weight_initial)
            if cyclecount >= weight_initial:
                return JsonResponse({
                    "error": f"Cycle count ({cyclecount}) must be less than current weight_initial ({weight_initial})."
                }, status=400)

            weight_final = weight_initial - cyclecount

            # Save new MQTTMessage for this cyclecount update
            mqtt_message = MQTTMessage.objects.create(
                device_id=device_id,
                weight_initial=weight_initial,
                weight_final=weight_final,
                cycle_number=cycle_number,
                timestamp=now(),
                topic=latest_entry.topic
            )

            # Save cycle info separately if you want
            Cycle.objects.create(
                device_id=device_id,
                cyclecount=str(cyclecount),
                remaining=str(weight_final)
            )

            return JsonResponse({
                "message": f"Cycle saved for device '{device_id}'.",
                "cycle_number": cycle_number,
                "weight_initial": weight_initial,
                "cyclecount": cyclecount,
                "weight_final": weight_final
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


























# old post cyclecount
# import json
# from django.views import View
# from django.http import JsonResponse
# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.timezone import now
# from app1.models import Cycle, MQTTMessage


# @method_decorator(csrf_exempt, name='dispatch')
# class SaveCycleCountView(View):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             device_id = data.get('device_id')
#             cyclecount = data.get('cyclecount')

#             if not device_id:
#                 return JsonResponse({"error": "Missing device_id."}, status=400)
#             if cyclecount is None:
#                 return JsonResponse({"error": "Missing cyclecount."}, status=400)

#             try:
#                 cyclecount = float(cyclecount)
#             except ValueError:
#                 return JsonResponse({"error": "Invalid cyclecount. Must be a number."}, status=400)

#             # Step 1: Get latest weight_initial for the device
#             latest_weight_initial_entry = MQTTMessage.objects.filter(
#                 device_id=device_id,
#                 weight_initial__isnull=False
#             ).order_by('-timestamp').first()

#             if not latest_weight_initial_entry:
#                 return JsonResponse({"error": "No weight_initial found for this device."}, status=404)

#             # Fix typo: weight_intial -> weight_initial
#             weight_initial = float(latest_weight_initial_entry.weight_initial)

#             # Step 2: Check if there's already a weight_final recorded for this cycle
#             latest_cycle_entry = MQTTMessage.objects.filter(
#                 device_id=device_id,
#                 weight_initial=weight_initial,
#                 weight_final__isnull=False
#             ).order_by('-timestamp').first()

#             if latest_cycle_entry:
#                 new_weight_initial = float(latest_cycle_entry.weight_final)
#                 cycle_number = latest_cycle_entry.cycle_number
#             else:
#                 new_weight_initial = weight_initial
#                 cycle_number = latest_weight_initial_entry.cycle_number + 1 if latest_weight_initial_entry.cycle_number else 1

#             # Ensure the posted cyclecount does not exceed the available weight
#             if cyclecount >= new_weight_initial:
#                 return JsonResponse({
#                     "error": f"Cycle count ({cyclecount}) must be less than available weight ({new_weight_initial})."
#                 }, status=400)

#             weight_final = new_weight_initial - cyclecount

#             # Save new MQTTMessage for this cycle
#             MQTTMessage.objects.create(
#                 device_id=device_id,
#                 weight_initial=new_weight_initial,
#                 weight_final=weight_final,
#                 cycle_number=cycle_number,
#                 timestamp=now(),
#                 topic=latest_weight_initial_entry.topic
#             )

#             # Save corresponding Cycle entry
#             Cycle.objects.create(
#                 device_id=device_id,
#                 cyclecount=str(cyclecount),
#                 remaining=str(weight_final)
#             )

#             return JsonResponse({
#                 "message": f"Cycle saved for device '{device_id}'.",
#                 "cycle_number": cycle_number,
#                 "weight_initial": new_weight_initial,
#                 "cyclecount": cyclecount,
#                 "weight_final": weight_final
#             }, status=201)

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)














# from django.views.decorators.csrf import csrf_exempt
# from .models import MQTTMessage, Cycle  
# @csrf_exempt
# def get_data(request):
#     if request.method=='GET':
#         cycle_qs = Cycle.objects.all().order_by('-timestamp')
#         mqtt_qs = MQTTMessage.objects.all().order_by('-timestamp')

#         # Serialize Cycle objects to dict list
#         cyclecount_map = {}
#         for c in cycle_qs:
#             # Keep the latest cyclecount for each device_id (based on timestamp order)
#             if c.device_id not in cyclecount_map:
#                 cyclecount_map[c.device_id] = c.cyclecount
            

#         # Serialize MQTTMessage objects to dict list
#         mqtt_data = []
#         for m in mqtt_qs:
#             cyclecount = cyclecount_map.get(m.device_id, '-')
#             mqtt_data.append({
#                 'device_id': m.device_id,
#                 # 'topic': m.topic,
#                 'weight_initial': m.weight_initial,
#                 'cyclecount': cyclecount,
#                 'weight_final': m.weight_final,
#                 'timestamp': m.timestamp.strftime("%b %d, %Y, %I:%M %p"),
#                 'cycle_number': m.cycle_number,
#                 # optionally add cyclecount from related Cycle if needed
#             })

#         # Combine into one JSON response
#         response_data = {
#             'mqtt_messages': mqtt_data,
#         }

#         return JsonResponse(response_data, safe=False)

#     return JsonResponse({"error": "Only GET method allowed."}, status=405)


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.timezone import now
from .models import MQTTMessage, Cycle

@csrf_exempt
def get_data(request):
    if request.method == 'GET':
        mqtt_qs = MQTTMessage.objects.all().order_by('-timestamp')

        mqtt_data = []
        for m in mqtt_qs:
            # Find most recent cycle entry
            recent_cycle = Cycle.objects.filter(
                device_id=m.device_id,
                timestamp__lte=m.timestamp
            ).order_by('-timestamp').first()

            if not recent_cycle:
                recent_cycle = Cycle.objects.filter(
                    device_id=m.device_id
                ).order_by('-timestamp').first()

            cyclecount = recent_cycle.cyclecount if recent_cycle else '-'

            # Find most recent cycle_status message
            recent_status = MQTTMessage.objects.filter(
                device_id=m.device_id,
                cycle_status__isnull=False,
                timestamp__lte=m.timestamp
            ).order_by('-timestamp').first()

            cycle_status = recent_status.cycle_status if recent_status else '-'

            mqtt_data.append({
                "device_id": m.device_id,
                "weight_initial": m.weight_initial,
                "weight_final": m.weight_final,
                "cyclecount": cyclecount,
                "cycle_status": cycle_status,
                "timestamp": m.timestamp.strftime("%b %d, %Y, %I:%M %p"),
                "cycle_number": m.cycle_number,
            })

        return JsonResponse({'mqtt_messages': mqtt_data}, safe=False)

    return JsonResponse({"error": "Only GET method allowed."}, status=405)
