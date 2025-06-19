
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
