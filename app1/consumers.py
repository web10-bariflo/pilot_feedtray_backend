
import json
import base64
import psycopg2
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class ThermalImageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "thermal_images_group"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        print("[✓] WebSocket connection established.")

        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "WebSocket connection established"
        }))

        self.send_task = asyncio.create_task(self.send_thermal_images_periodically())
        self.ping_task = asyncio.create_task(self.send_ping_periodically())

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'send_task') and self.send_task:
                self.send_task.cancel()
                try:
                    await self.send_task
                except asyncio.CancelledError:
                    pass

            if hasattr(self, 'ping_task') and self.ping_task:
                self.ping_task.cancel()
                try:
                    await self.ping_task
                except asyncio.CancelledError:
                    pass

            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print("[!] WebSocket disconnected.")
        except Exception as e:
            print(f"[ERROR] Error during WebSocket disconnection: {e}")
        finally:
            await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))
            print("[↔] Ping received, Pong sent.")

    async def send_ping_periodically(self):
        while True:
            try:
                await self.send(text_data=json.dumps({
                    'type': 'ping'
                }))
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[PING ERROR] {e}")
                break

    async def send_thermal_images(self):
        try:
            conn = psycopg2.connect(
                dbname="checktray",
                user="Vertoxlabs",
                password="Vtx@2025",
                host="bcpostgressqlserver.postgres.database.azure.com",
                port="5432"
            )
            cur = conn.cursor()
            cur.execute("SELECT node_id, thermal_image, colour_image, created_at FROM check_tray_app_projectdata ORDER BY created_at DESC LIMIT 20")

            records = cur.fetchall()

            thermal_data = []
            colour_data = []

            for idx, row in enumerate(records, start=1):
                print(f"\n[INFO] Processing Record #{idx}")
                node_id, thermal_image_data, colour_image_data, created_at = row

                # Thermal image block
                if thermal_image_data:
                    try:
                        if isinstance(thermal_image_data, str):
                            thermal_image_data = thermal_image_data.encode('utf-8')
                        encoded = base64.b64encode(thermal_image_data).decode('utf-8')
                        thermal_data.append({
                            'node_id': node_id,
                            'created_at': created_at.isoformat(),
                            'thermal_image': encoded
                        })
                        print(f"[✓] Thermal image sent for node_id: {node_id}")
                    except Exception as e:
                        print(f"[ERROR] Thermal image encode failed for node_id {node_id}: {e}")
                else:
                    print(f"[INFO] No thermal image for node_id: {node_id}")

                # Colour image block
                if colour_image_data:
                    try:
                        if isinstance(colour_image_data, str):
                            colour_image_data = colour_image_data.encode('utf-8')
                        encoded = base64.b64encode(colour_image_data).decode('utf-8')
                        colour_data.append({
                            'node_id': node_id,
                            'created_at': created_at.isoformat(),
                            'colour_image': encoded
                        })
                        print(f"[✓] Colour image sent for node_id: {node_id}")
                    except Exception as e:
                        print(f"[ERROR] Colour image encode failed for node_id {node_id}: {e}")
                else:
                    print(f"[INFO] No colour image for node_id: {node_id}")

            cur.close()
            conn.close()

            # Send thermal images
            if thermal_data:
                await self.send(text_data=json.dumps({
                    'type': 'thermal_images',
                    'data': thermal_data
                }))

            # Send colour images
            if colour_data:
                await self.send(text_data=json.dumps({
                    'type': 'colour_images',
                    'data': colour_data
                }))

            print(f"[✓] Sent {len(thermal_data)} thermal and {len(colour_data)} colour images to WebSocket")

        except Exception as e:
            print(f"[CRITICAL] Error fetching images: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to fetch images.'
            }))

    async def send_thermal_images_periodically(self):
        try:
            while True:
                await self.send_thermal_images()
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            print("[INFO] Background image task cancelled due to disconnect.")
        except Exception as e:
            print(f"[ERROR] Periodic image sending failed: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'An error occurred while sending images.'
            }))
