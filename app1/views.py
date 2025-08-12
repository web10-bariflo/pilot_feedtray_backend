
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from .models import *
import base64
import psycopg2
import threading
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from django.utils.timezone import localtime
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.http import HttpResponse, JsonResponse
from django.utils.dateparse import parse_date
import csv, json

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import *
import json
import traceback
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt







@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("🔵 Received data:", data)

            device_id = data.get('Device_id')
            user_name = data.get('User_name')
            password = data.get('password')
            mob = data.get('Mob')
            email = data.get('Email')

            if not all([device_id, user_name, mob, email]):
                return JsonResponse({'error': 'Device_id, User_name, Mob, and Email are required.'}, status=400)

            if MyUser.objects.filter(Device_id=device_id).exists():
                return JsonResponse({'error': 'Device_id already exists.'}, status=409)

            if MyUser.objects.filter(Mob=mob).exists():
                return JsonResponse({'error': 'Mobile number already registered.'}, status=409)

            if MyUser.objects.filter(Email=email).exists():
                return JsonResponse({'error': 'Email already registered.'}, status=409)

            user = MyUser.objects.create(
                Device_id=device_id,
                User_name=user_name,
                password=password,
                Mob=mob,
                Email=email
            )

            return JsonResponse({
                'message': 'User created successfully.',
                'Device_id': user.Device_id,
                'User_name': user.User_name,
                'Mob': user.Mob,
                'Email': user.Email
            }, status=201)

        except Exception as e:
            print("🔥 Exception:", str(e))
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method. Use POST.'}, status=405)



@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            identifier = data.get('identifier')
            password = data.get('password')

            if not all([identifier, password]):
                return JsonResponse({'error': 'Username/Email/Mobile and password are required.'}, status=400)

            try:
                # Determine login method
                if identifier.isdigit():
                    user = MyUser.objects.get(Mob=int(identifier))
                elif '@' in identifier:
                    user = MyUser.objects.get(Email=identifier)
                else:
                    user = MyUser.objects.get(User_name=identifier)

                if user.password == password:
                    return JsonResponse({
                        'message': 'Login successful',
                        'Device_id': user.Device_id,
                        'User_name': user.User_name,
                        'Mob': user.Mob,
                        'Email': user.Email
                    }, status=200)
                else:
                    return JsonResponse({'error': 'Invalid password'}, status=401)

            except MyUser.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def forgot_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({'error': 'Email is required.'}, status=400)

            try:
                user = MyUser.objects.get(Email=email)
                reset_link = f"{settings.BASE_URL}/reset-password/?email={user.Email}"


                from django.core.mail import send_mail
                send_mail(
                    subject="Reset Your Password",
                    message=f"Hi {user.User_name},\n\nClick the link to reset your password:\n{reset_link}",
                    from_email="care.bariflolabs@gmail.com",
                    recipient_list=[user.Email],
                    fail_silently=False,
                )


                return JsonResponse({'message': 'Reset link sent to your email.'}, status=200)

            except MyUser.DoesNotExist:
                return JsonResponse({'error': 'Email not found.'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@csrf_exempt
def reset_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            new_password = data.get('new_password')

            if not all([email, new_password]):
                return JsonResponse({'error': 'Email and new password are required.'}, status=400)

            try:
                user = MyUser.objects.get(Email=email)
                user.password = new_password
                user.save()
                return JsonResponse({'message': 'Password updated successfully.'}, status=200)

            except MyUser.DoesNotExist:
                return JsonResponse({'error': 'User with this email not found.'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)




@csrf_exempt
def reset_password_page(request):
    email = request.GET.get('email', '')
    return render(request, 'reset_password.html', {'email': email})




















# MQTT to receive 'all cycle completed' and update end_time
def subscribe_and_mark_end():
    def on_connect(client, userdata, flags, rc):
        print("MQTT connected:", rc)
        client.subscribe("feeder/fdtryA00/cycle_status")

    def on_message(client, userdata, msg):
        message = msg.payload.decode().lower()
        print("MQTT message received:", message)
        if 'all cycle completed' in message:
            try:
                latest = Cycle.objects.latest('timestamp')
                latest.end_time = datetime.now()
                latest.save()
                print("End time updated successfully.")
            except Exception as e:
                print("Error setting end_time:", e)

    client = mqtt.Client()
    client.username_pw_set("mqttuser", "Bfl@2025")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mqttbroker.bc-pl.com", 1883, 60)
    client.loop_start()


@csrf_exempt
def handle_cycle(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cyclecount = data.get('cyclecount')

            if cyclecount is None:
                return JsonResponse({'error': 'cyclecount is required'}, status=400)

            # Step 1: Save cyclecount with start_time
            cycle = Cycle.objects.create(
                cyclecount=cyclecount,
                start_time=now()
            )
            print(f"New cycle created: ID={cycle.id}, count={cycle.cyclecount}")

            # Step 3: Start MQTT listener in background
            threading.Thread(target=subscribe_and_mark_end, daemon=True).start()

            return JsonResponse({'message': 'Cycle created. Image fetch and MQTT started.'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)




@require_GET
def get_latest_cycles(request):
    try:
        recent_cycles = Cycle.objects.order_by('-timestamp')[:10]
        data = [{
            'id': c.id,
            'cyclecount': c.cyclecount,
            'start_time': localtime(c.start_time).strftime('%Y-%m-%d %H:%M:%S') if c.start_time else None,
            'end_time': localtime(c.end_time).strftime('%Y-%m-%d %H:%M:%S') if c.end_time else None,
            'timestamp': localtime(c.timestamp).strftime('%Y-%m-%d %H:%M:%S') if c.timestamp else None,
        } for c in recent_cycles]

        return JsonResponse({'recent_cycles': data}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    





@require_GET
def get_all_cycles(request):
    try:
        all_cycles = Cycle.objects.order_by('-timestamp')

        data = [{
            'id': c.id,
            'cyclecount': c.cyclecount,
            'start_time': localtime(c.start_time).strftime('%Y-%m-%d %H:%M:%S') if c.start_time else None,
            'end_time': localtime(c.end_time).strftime('%Y-%m-%d %H:%M:%S') if c.end_time else None,
            'timestamp': localtime(c.timestamp).strftime('%Y-%m-%d %H:%M:%S') if c.timestamp else None,
        } for c in all_cycles]

        return JsonResponse(data, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





@csrf_exempt
def download_cycles_csv(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        body = json.loads(request.body)
        from_date = body.get('from_date')
        to_date = body.get('to_date')
    except Exception as e:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Parse dates
    from_dt = parse_date(from_date) if from_date else None
    to_dt = parse_date(to_date) if to_date else None

    # Get filtered queryset
    cycles = Cycle.objects.all()
    if from_dt and to_dt:
        cycles = cycles.filter(timestamp__date__gte=from_dt, timestamp__date__lte=to_dt)
    cycles = cycles.order_by('-timestamp')

    # Prepare CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cycles.csv"'

    writer = csv.writer(response)
    writer.writerow(['S.No', 'Cycle Count', 'Start Time', 'End Time', 'Timestamp'])

    for idx, cycle in enumerate(cycles, start=1):
        writer.writerow([
            idx,
            cycle.cyclecount,
            cycle.start_time.strftime('%Y-%m-%d %H:%M:%S') if cycle.start_time else '',
            cycle.end_time.strftime('%Y-%m-%d %H:%M:%S') if cycle.end_time else '',
            cycle.timestamp.strftime('%Y-%m-%d %H:%M:%S') if cycle.timestamp else ''
        ])

    return response

######################################## scheduling #############################


# from django.db.models import Q
# from django.db.models.functions import Trim
# import json
# import threading
# import paho.mqtt.client as mqtt
# from django.views.decorators.csrf import csrf_exempt
# from django.utils import timezone
# from django.http import JsonResponse
# from .models import Scheduling

# # MQTT Configuration
# MQTT_BROKER = 'mqttbroker.bc-pl.com'
# MQTT_PORT = 1883
# MQTT_USER = 'mqttuser'
# MQTT_PASSWORD = 'Bfl@2025'
# DEVICE_ID = 'fdtryA00'
# STATUS_TOPIC = f"feeder/{DEVICE_ID}/cycle_status"
# ABORT_TOPIC = f"feeder/{DEVICE_ID}/cycle_abort"

# # Global MQTT client
# mqtt_client = None

# # Global variable to track the running schedule
# current_running_id = None

# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("Connected to MQTT broker.")
#         client.subscribe(STATUS_TOPIC)
#         client.subscribe(ABORT_TOPIC)
#     else:
#         print(f"Failed to connect, return code {rc}")



# def mark_due_schedule_running():
#     global current_running_id
#     now_time = timezone.now()

#     # Pick the next due schedule that hasn't run yet
#     next_schedule = Scheduling.objects.filter(
#         start_time__lte=now_time,
#         is_running=False,
#         status=''  # or whatever indicates "not completed"
#     ).order_by('start_time').first()

#     if next_schedule:
#         next_schedule.is_running = True
#         next_schedule.save(update_fields=['is_running'])
#         current_running_id = next_schedule.id
#         print(f"[RUNNING] Schedule ID={current_running_id} started at {now_time}")
#     else:
#         current_running_id = None
#         print("[DEBUG] No schedule ready to run")



# def start_next_schedule():
#     global current_running_id
#     if current_running_id:
#         return  # already tracking one

#     now_time = timezone.now()
#     next_schedule = (
#         Scheduling.objects.filter(
#             Q(status__isnull=True) | Q(status=''),
#             start_time__lte=now_time,
#             is_running=False
#         )
#         .order_by('start_time')
#         .first()
#     )
#     if next_schedule:
#         next_schedule.is_running = True
#         next_schedule.save(update_fields=['is_running'])
#         current_running_id = next_schedule.id
#         print(f"Started schedule {next_schedule.id}")

# def on_message(client, userdata, msg):
#     global current_running_id
#     message = msg.payload.decode().strip()
#     now_time = timezone.now()

#     print(f"\n[MQTT MESSAGE] Topic={msg.topic}, Payload='{message}', CurrentRunningID={current_running_id}")

#     if current_running_id is None:
#         print("[DEBUG] No schedule running, ignoring message.")
#         return

#     try:
#         schedule = Scheduling.objects.get(id=current_running_id)
#     except Scheduling.DoesNotExist:
#         print(f"[WARNING] Schedule ID={current_running_id} not found")
#         current_running_id = None
#         return

#     # Only process completion or abort for the *current* schedule
#     if msg.topic == STATUS_TOPIC and message.lower() == "all cycles completed successfully":
#         schedule.status = timezone.localtime(now_time).strftime('%d/%m/%Y, %I:%M:%S %p')
#         schedule.is_running = False
#         schedule.save(update_fields=['status', 'is_running'])
#         print(f"[COMPLETED] Schedule ID={schedule.id} marked as COMPLETED")

#         # Now free the current_running_id
#         current_running_id = None

#         # Start the next task ONLY after current task is cleared
#         mark_due_schedule_running()

#     elif msg.topic == ABORT_TOPIC:
#         schedule.status = "Aborted"
#         schedule.is_running = False
#         schedule.save(update_fields=['status', 'is_running'])
#         print(f"[ABORTED] Schedule ID={schedule.id} marked as ABORTED")

#         # Free current_running_id and pick next
#         current_running_id = None
#         mark_due_schedule_running()

#     else:
#         print("[DEBUG] Message ignored (not a completion or abort).")






# def start_mqtt_client():
#     global mqtt_client
#     mqtt_client = mqtt.Client()
#     mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
#     mqtt_client.on_connect = on_connect
#     mqtt_client.on_message = on_message
#     mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
#     mqtt_client.loop_start()


# # Start MQTT client on server boot if not already running
# if mqtt_client is None:
#     threading.Thread(target=start_mqtt_client).start()


# @csrf_exempt
# def create_schedule(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             schedule_id = data.get('schedule_id')
#             start_time_str = data.get('start_time')  # 'YYYY-MM-DD HH:MM'
#             cyclecount = data.get('cyclecount')
#             recurring_hours = data.get('recurring_hours')

#             # Validate required fields
#             if not all([schedule_id, start_time_str, cyclecount is not None, recurring_hours is not None]):
#                 return JsonResponse({'error': 'Missing required fields'}, status=400)

#             # Parse and localize start_time
#             try:
#                 start_time = timezone.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
#                 start_time = timezone.make_aware(start_time, timezone.get_current_timezone())
#             except ValueError:
#                 return JsonResponse({'error': 'Invalid start_time format. Use YYYY-MM-DD HH:MM'}, status=400)

#             # Calculate lock period for the new schedule
#             new_end_time = start_time + timezone.timedelta(minutes=int(cyclecount) * 2)

#             # Check for conflicts with existing schedules (only if NOT aborted)
#             existing_schedules = Scheduling.objects.exclude(status__iexact="Aborted")
#             for sched in existing_schedules:
#                 sched_end_time = sched.start_time + timezone.timedelta(minutes=(int(sched.cyclecount) * 2) + 1)

#                 # Overlap check: new schedule starts before existing ends, and new ends after existing starts
#                 if start_time < sched_end_time and new_end_time > sched.start_time:
#                     return JsonResponse({'error': 'Schedule conflict: Overlaps with an existing active schedule'}, status=409)

#             # Create the schedule if no conflict
#             schedule = Scheduling.objects.create(
#                 schedule_id=schedule_id,
#                 start_time=start_time,
#                 cyclecount=cyclecount,
#                 recurring_hours=recurring_hours,
#                 is_running=False  # ensure default
#             )

#             return JsonResponse({'status': 'success', 'id': schedule.id})

#         except json.JSONDecodeError:
#             return JsonResponse({'error': 'Invalid JSON'}, status=400)

#     return JsonResponse({'error': 'Method not allowed'}, status=405)


# # Publishing utilities
# def publish_cycle_status():
#     if mqtt_client:
#         mqtt_client.publish(STATUS_TOPIC, "All Cycles Completed Successfully")


# def publish_cycle_abort():
#     if mqtt_client:
#         mqtt_client.publish(ABORT_TOPIC, "Aborted")



############################################## 12-08-2025


from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Scheduling
import json
import threading
import time
import paho.mqtt.client as mqtt
import threading
# MQTT Configuration
MQTT_BROKER = 'mqttbroker.bc-pl.com'
MQTT_PORT = 1883
MQTT_USER = 'mqttuser'
MQTT_PASSWORD = 'Bfl@2025'
DEVICE_ID = 'fdtryA00'
STATUS_TOPIC = f"feeder/{DEVICE_ID}/cycle_status"
ABORT_TOPIC = f"feeder/{DEVICE_ID}/cycle_abort"

# Global vars
# Global vars
mqtt_client = None
current_running_id = None
CHECK_INTERVAL = 5  # seconds

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(STATUS_TOPIC)
        client.subscribe(ABORT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def pick_next_schedule():
    global current_running_id

    # Avoid picking a new schedule if one is still running
    if current_running_id:
        print(f"[INFO] A schedule is already running (ID={current_running_id}), skipping pick.")
        return

    now_time = timezone.localtime(timezone.now())
    next_schedule = (
        Scheduling.objects
        .filter(start_time__lte=now_time, is_running=False, status__isnull=True)
        .order_by('start_time', 'id')
        .first()
    )

    if next_schedule:
        next_schedule.is_running = True
        next_schedule.save(update_fields=['is_running'])
        current_running_id = next_schedule.id

        print(f"[STARTED] Schedule ID={current_running_id} started at {now_time}")
        # 🚀 Trigger the actual work — for example send MQTT start signal here
        # client.publish(START_TOPIC, payload="Start", qos=1)
    else:
        print("[INFO] No schedules ready to start.")


def scheduler_loop():
    """Background loop to continuously check and start due schedules."""
    while True:
        try:
            pick_next_schedule()
        except Exception as e:
            print(f"[ERROR] Scheduler loop: {e}")
        time.sleep(CHECK_INTERVAL)

def on_message(client, userdata, msg):
    global current_running_id
    message = msg.payload.decode().strip()
    now_time = timezone.now()

    print(f"\n[MQTT MESSAGE] Topic={msg.topic}, Payload='{message}'")

    # Make sure we have a specific schedule we're tracking
    if not current_running_id:
        print("[DEBUG] No running schedule ID stored, ignoring message.")
        return

    try:
        schedule = Scheduling.objects.get(id=current_running_id)
    except Scheduling.DoesNotExist:
        print(f"[WARNING] Schedule ID={current_running_id} not found in DB.")
        return

    # Completion message handling
    if msg.topic == STATUS_TOPIC and message.lower() == "all cycles completed successfully".lower():
        schedule.status = timezone.localtime(now_time).strftime('%d/%m/%Y, %I:%M:%S %p')
        schedule.save(update_fields=['status'])
        print(f"[COMPLETED] Schedule ID={schedule.id} status set to COMPLETED")

        def delayed_stop(sched_id):
            global current_running_id
            time.sleep(3)
            try:
                sched = Scheduling.objects.get(id=sched_id)
                sched.is_running = False
                sched.save(update_fields=['is_running'])
                print(f"[INFO] Schedule ID={sched_id} is_running set to False after delay")
            except Scheduling.DoesNotExist:
                print(f"[WARNING] Schedule ID={sched_id} not found during delayed stop")
            finally:
                current_running_id = None
                pick_next_schedule()

        threading.Thread(target=delayed_stop, args=(schedule.id,), daemon=True).start()

    elif msg.topic == ABORT_TOPIC:
        schedule.status = "Aborted"
        schedule.save(update_fields=['status'])
        print(f"[ABORTED] Schedule ID={schedule.id} status set to ABORTED")

        def delayed_abort(sched_id):
            global current_running_id
            time.sleep(3)
            try:
                sched = Scheduling.objects.get(id=sched_id)
                sched.is_running = False
                sched.save(update_fields=['is_running'])
                print(f"[INFO] Schedule ID={sched_id} is_running set to False after delay")
            except Scheduling.DoesNotExist:
                print(f"[WARNING] Schedule ID={sched_id} not found during delayed abort")
            finally:
                current_running_id = None
                pick_next_schedule()

        threading.Thread(target=delayed_abort, args=(schedule.id,), daemon=True).start()

    else:
        print("[DEBUG] Message ignored (not a completion or abort).")


def start_mqtt_client():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

# Start background services
if mqtt_client is None:
    threading.Thread(target=start_mqtt_client, daemon=True).start()
    threading.Thread(target=scheduler_loop, daemon=True).start()

@csrf_exempt
def create_schedule(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            schedule_id = data.get('schedule_id')
            start_time_str = data.get('start_time')
            cyclecount = data.get('cyclecount')
            recurring_hours = data.get('recurring_hours')

            if not all([schedule_id, start_time_str, cyclecount is not None, recurring_hours is not None]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            try:
                start_time = timezone.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
                start_time = timezone.make_aware(start_time, timezone.get_current_timezone())
            except ValueError:
                return JsonResponse({'error': 'Invalid start_time format. Use YYYY-MM-DD HH:MM'}, status=400)

            new_end_time = start_time + timezone.timedelta(minutes=int(cyclecount) * 2)
            existing_schedules = Scheduling.objects.exclude(status__iexact="Aborted")

            for sched in existing_schedules:
                sched_end_time = sched.start_time + timezone.timedelta(minutes=(int(sched.cyclecount) * 2) + 1)
                if start_time < sched_end_time and new_end_time > sched.start_time:
                    return JsonResponse({'error': 'Schedule conflict: Overlaps with an existing active schedule'}, status=409)

            schedule = Scheduling.objects.create(
                schedule_id=schedule_id,
                start_time=start_time,
                cyclecount=cyclecount,
                recurring_hours=recurring_hours,
                is_running=False
            )

            return JsonResponse({'status': 'success', 'id': schedule.id})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Publishing utilities
def publish_cycle_status():
    if mqtt_client:
        mqtt_client.publish(STATUS_TOPIC, "All Cycles Completed Successfully")

def publish_cycle_abort():
    if mqtt_client:
        mqtt_client.publish(ABORT_TOPIC, "Aborted")



def get_all_schedules(request):
    if request.method == 'GET':
        schedules = list(
            Scheduling.objects.all()
            .order_by('-timestamp')
            .values(
                'id',
                'schedule_id',
                'start_time',
                'cyclecount',
                'recurring_hours',
                'timestamp',
                'status'
            )
        )
        # import json
        # print("DEBUG get_all_schedules JSON:", json.dumps(schedules, indent=2, default=str))
        return JsonResponse({'schedules': schedules})


from django.db.models import Q

def get_all_schedule_ids(request):
    if request.method == 'GET':
        current_time = now()
        # Only future schedules AND status does not contain "aborted"
        upcoming_schedules = Scheduling.objects.filter(
            start_time__gt=current_time
        ).exclude(
            Q(status__icontains="aborted")
        )
        
        schedule_ids = list(
            upcoming_schedules.values_list('schedule_id', flat=True).distinct()
        )
        return JsonResponse({'schedule_ids': schedule_ids})

@csrf_exempt
def delete_schedule_by_id(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            schedule_id = data.get('schedule_id')

            if not schedule_id:
                return JsonResponse({'error': 'schedule_id is required'}, status=400)

            deleted_count, _ = Scheduling.objects.filter(schedule_id=schedule_id).delete()

            if deleted_count == 0:
                return JsonResponse({'message': 'No matching schedule found'}, status=404)

            return JsonResponse({'message': f'Successfully deleted {deleted_count} record(s)'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


######################################## websocket ###############################################

from django.core.cache import cache

@csrf_exempt
def upload_project_data(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            node_id = data.get('node_id')
            thermal_image_base64 = data.get('thermal_image')
            colour_image_base64 = data.get('colour_image')

            image_urls = {}

            # Save thermal image if provided
            if thermal_image_base64:
                thermal_image_data = base64.b64decode(thermal_image_base64)
                thermal_image_name = f"thermal_image_{node_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpeg"
                thermal_images_dir = "media/thermal_images"
                os.makedirs(thermal_images_dir, exist_ok=True)
                thermal_image_path = os.path.join(thermal_images_dir, thermal_image_name)
                with open(thermal_image_path, 'wb') as f:
                    f.write(thermal_image_data)
                thermal_image_url = f"http://104.43.56.211/media/thermal_images/{thermal_image_name}"
                image_urls['thermal_image_url'] = thermal_image_url
                cache.set('latest_image_url', thermal_image_url, timeout=None)

            # Save color image if provided
            if colour_image_base64:
                colour_image_data = base64.b64decode(colour_image_base64)
                colour_image_name = f"colour_image_{node_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpeg"
                colour_images_dir = "media/colour_images"
                os.makedirs(colour_images_dir, exist_ok=True)
                colour_image_path = os.path.join(colour_images_dir, colour_image_name)
                with open(colour_image_path, 'wb') as f:
                    f.write(colour_image_data)
                colour_image_url = f"http://104.43.56.211/media/colour_images/{colour_image_name}"
                image_urls['colour_image_url'] = colour_image_url
                cache.set('latest_colour_image_url', colour_image_url, timeout=None)

            return JsonResponse({'status': 'success', **image_urls})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})


def event_stream(request):
    """
    This view will stream the latest image URL to the frontend via SSE.
    """
    def generate():
        while True:
            image_url = cache.get('latest_image_url')
            if image_url:
                print(f"Sending SSE event: {image_url}")  # Log the event being sent
                yield f"data: {image_url}\n\n"
            else:
                print("No image URL in cache yet.")  # Log if no image URL is available
            time.sleep(1)  # Sleep to prevent overwhelming the server

    return HttpResponse(generate(), content_type='text/event-stream')




import os
import io
import zipfile
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def download_all_images_combined(request):
    try:
        thermal_dir = "media/thermal_images"
        colour_dir = "media/colour_images"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            # Add thermal images
            for filename in os.listdir(thermal_dir):
                file_path = os.path.join(thermal_dir, filename)
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        # Add just the filename (no subfolder)
                        zip_file.writestr(filename, f.read())

            # Add colour images
            for filename in os.listdir(colour_dir):
                file_path = os.path.join(colour_dir, filename)
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        # Add just the filename (no subfolder)
                        zip_file.writestr(filename, f.read())

        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=all_images_combined.zip'
        return response

    except Exception as e:
        return HttpResponse(f"Error creating zip: {e}", status=500)
