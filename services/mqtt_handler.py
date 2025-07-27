"""
MQTT Handler for WasteWise IoT Sensor Data

This service handles incoming MQTT messages from ESP32 sensors
monitoring waste bins and processes the data in real-time.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
from django.conf import settings
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

logger = logging.getLogger('wastewise.mqtt')


class MQTTHandler:
    """
    MQTT client handler for processing IoT sensor data
    
    Handles connections to MQTT broker, processes incoming sensor data,
    and manages real-time updates to the web dashboard.
    """
    
    def __init__(self):
        self.client = None
        self.channel_layer = get_channel_layer()
        self.is_connected = False
        
        # MQTT configuration from Django settings
        self.broker_host = getattr(settings, 'MQTT_BROKER_HOST', 'localhost')
        self.broker_port = getattr(settings, 'MQTT_BROKER_PORT', 1883)
        self.username = getattr(settings, 'MQTT_USERNAME', '')
        self.password = getattr(settings, 'MQTT_PASSWORD', '')
        self.topics = getattr(settings, 'MQTT_TOPICS', {
            'sensor_data': 'wastewise/sensors/+/data',
            'alerts': 'wastewise/alerts/+',
            'status': 'wastewise/sensors/+/status',
        })
    
    def initialize_client(self):
        """Initialize MQTT client with configuration"""
        self.client = mqtt.Client()
        
        # Set authentication if provided
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # Set callback functions
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        
        return self.client
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to all configured topics
            for topic_name, topic_pattern in self.topics.items():
                client.subscribe(topic_pattern)
                logger.info(f"Subscribed to {topic_name}: {topic_pattern}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        self.is_connected = False
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for subscription confirmation"""
        logger.info(f"Subscription confirmed with QoS: {granted_qos}")
    
    def on_message(self, client, userdata, msg):
        """
        Main message handler for incoming MQTT messages
        
        Routes messages to appropriate handlers based on topic pattern.
        """
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received message on topic: {topic}")
            
            # Route to appropriate handler based on topic
            if '/data' in topic:
                self.handle_sensor_data(topic, payload)
            elif '/status' in topic:
                self.handle_sensor_status(topic, payload)
            elif '/alerts' in topic:
                self.handle_sensor_alert(topic, payload)
            else:
                logger.warning(f"Unknown topic pattern: {topic}")
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def handle_sensor_data(self, topic: str, payload: str):
        """
        Handle sensor data messages
        
        Expected topic format: wastewise/sensors/{device_id}/data
        Expected payload: JSON with sensor readings
        """
        try:
            # Extract device ID from topic
            topic_parts = topic.split('/')
            if len(topic_parts) < 3:
                logger.error(f"Invalid sensor data topic format: {topic}")
                return
            
            device_id = topic_parts[2]
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in sensor data: {e}")
                return
            
            # Validate required fields
            required_fields = ['fill_level', 'battery_level', 'timestamp']
            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in sensor data: {data}")
                return
            
            # Process the sensor data asynchronously
            asyncio.create_task(self.process_sensor_data_async(device_id, data))
            
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")
    
    async def process_sensor_data_async(self, device_id: str, data: Dict[str, Any]):
        """Process sensor data asynchronously"""
        try:
            from apps.wastewise.sensors.models import SensorDevice, SensorReading
            from apps.wastewise.bins.models import WasteBin
            
            # Get or create sensor device
            device = await sync_to_async(SensorDevice.objects.select_related('bin').get)(
                device_id=device_id
            )
            
            if not device:
                logger.error(f"Device not found: {device_id}")
                return
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                timestamp = timezone.make_aware(timestamp) if timezone.is_naive(timestamp) else timestamp
            except (ValueError, KeyError):
                timestamp = timezone.now()
            
            # Create sensor reading
            reading = await sync_to_async(SensorReading.objects.create)(
                device=device,
                bin=device.bin,
                fill_level=data['fill_level'],
                distance_cm=data.get('distance_cm'),
                temperature=data.get('temperature'),
                humidity=data.get('humidity'),
                battery_level=data['battery_level'],
                signal_strength=data.get('signal_strength'),
                additional_data=data.get('additional_data', {}),
                timestamp=timestamp
            )
            
            # Update device last seen
            device.last_seen = timezone.now()
            await sync_to_async(device.save)(update_fields=['last_seen'])
            
            # Check for alerts
            await self.check_and_create_alerts(device, reading)
            
            # Send real-time update to dashboard
            await self.send_realtime_update('sensor_data', {
                'device_id': device_id,
                'bin_id': device.bin.bin_id,
                'fill_level': reading.fill_level,
                'battery_level': reading.battery_level,
                'timestamp': reading.timestamp.isoformat(),
                'location': {
                    'lat': device.bin.latitude,
                    'lng': device.bin.longitude,
                } if device.bin.location else None
            })
            
            logger.info(f"Processed sensor data for device {device_id}")
            
        except Exception as e:
            logger.error(f"Error processing sensor data for {device_id}: {e}")
    
    async def check_and_create_alerts(self, device, reading):
        """Check sensor reading and create alerts if necessary"""
        try:
            from apps.wastewise.sensors.models import SensorAlert
            
            alerts_to_create = []
            
            # Check for full bin
            if reading.fill_level >= 95:
                alerts_to_create.append({
                    'alert_type': 'bin_overflow',
                    'severity': 'critical',
                    'title': f'Bin {device.bin.bin_id} Overflow Alert',
                    'message': f'Bin is {reading.fill_level}% full and may be overflowing'
                })
            elif reading.fill_level >= 85:
                alerts_to_create.append({
                    'alert_type': 'bin_full',
                    'severity': 'high',
                    'title': f'Bin {device.bin.bin_id} Full Alert',
                    'message': f'Bin is {reading.fill_level}% full and needs collection'
                })
            
            # Check for low battery
            if reading.battery_level <= 10:
                alerts_to_create.append({
                    'alert_type': 'low_battery',
                    'severity': 'medium',
                    'title': f'Low Battery - Device {device.device_id}',
                    'message': f'Device battery is at {reading.battery_level}%'
                })
            
            # Check for data anomaly
            if reading.is_anomaly:
                alerts_to_create.append({
                    'alert_type': 'data_anomaly',
                    'severity': 'medium',
                    'title': f'Data Anomaly - Device {device.device_id}',
                    'message': f'Anomalous reading detected: {reading.anomaly_reason}'
                })
            
            # Create alerts
            for alert_data in alerts_to_create:
                # Check if similar alert already exists
                existing_alert = await sync_to_async(
                    SensorAlert.objects.filter(
                        device=device,
                        alert_type=alert_data['alert_type'],
                        is_active=True
                    ).exists
                )()
                
                if not existing_alert:
                    alert = await sync_to_async(SensorAlert.objects.create)(
                        device=device,
                        bin=device.bin,
                        reading=reading,
                        **alert_data
                    )
                    
                    # Send real-time alert
                    await self.send_realtime_update('alert', {
                        'alert_id': str(alert.id),
                        'device_id': device.device_id,
                        'bin_id': device.bin.bin_id,
                        'alert_type': alert.alert_type,
                        'severity': alert.severity,
                        'title': alert.title,
                        'message': alert.message,
                        'timestamp': alert.created_at.isoformat()
                    })
            
        except Exception as e:
            logger.error(f"Error checking alerts for device {device.device_id}: {e}")
    
    def handle_sensor_status(self, topic: str, payload: str):
        """Handle sensor status messages"""
        try:
            topic_parts = topic.split('/')
            device_id = topic_parts[2]
            
            data = json.loads(payload)
            
            # Update device status asynchronously
            asyncio.create_task(self.update_device_status_async(device_id, data))
            
        except Exception as e:
            logger.error(f"Error handling sensor status: {e}")
    
    async def update_device_status_async(self, device_id: str, data: Dict[str, Any]):
        """Update device status asynchronously"""
        try:
            from apps.wastewise.sensors.models import SensorDevice
            
            device = await sync_to_async(SensorDevice.objects.get)(device_id=device_id)
            
            # Update device status
            if 'status' in data:
                device.status = data['status']
            if 'battery_level' in data:
                device.battery_level = data['battery_level']
            if 'signal_strength' in data:
                device.signal_strength = data['signal_strength']
            
            device.last_seen = timezone.now()
            await sync_to_async(device.save)()
            
            logger.info(f"Updated status for device {device_id}")
            
        except Exception as e:
            logger.error(f"Error updating device status for {device_id}: {e}")
    
    def handle_sensor_alert(self, topic: str, payload: str):
        """Handle sensor alert messages"""
        try:
            topic_parts = topic.split('/')
            device_id = topic_parts[2]
            
            data = json.loads(payload)
            
            # Process alert asynchronously
            asyncio.create_task(self.process_sensor_alert_async(device_id, data))
            
        except Exception as e:
            logger.error(f"Error handling sensor alert: {e}")
    
    async def process_sensor_alert_async(self, device_id: str, data: Dict[str, Any]):
        """Process sensor alert asynchronously"""
        try:
            from apps.wastewise.sensors.models import SensorDevice, SensorAlert
            
            device = await sync_to_async(SensorDevice.objects.select_related('bin').get)(
                device_id=device_id
            )
            
            # Create alert
            alert = await sync_to_async(SensorAlert.objects.create)(
                device=device,
                bin=device.bin,
                alert_type=data.get('alert_type', 'sensor_error'),
                severity=data.get('severity', 'medium'),
                title=data.get('title', f'Alert from {device_id}'),
                message=data.get('message', 'Sensor reported an alert')
            )
            
            # Send real-time alert
            await self.send_realtime_update('alert', {
                'alert_id': str(alert.id),
                'device_id': device_id,
                'bin_id': device.bin.bin_id,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.created_at.isoformat()
            })
            
            logger.info(f"Processed alert from device {device_id}")
            
        except Exception as e:
            logger.error(f"Error processing alert from {device_id}: {e}")
    
    async def send_realtime_update(self, update_type: str, data: Dict[str, Any]):
        """Send real-time updates to WebSocket consumers"""
        if self.channel_layer:
            try:
                await self.channel_layer.group_send(
                    'dashboard_updates',
                    {
                        'type': 'send_update',
                        'update_type': update_type,
                        'data': data
                    }
                )
            except Exception as e:
                logger.error(f"Error sending real-time update: {e}")
    
    def start(self):
        """Start the MQTT client"""
        try:
            self.initialize_client()
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            logger.info("MQTT handler started")
        except Exception as e:
            logger.error(f"Error starting MQTT handler: {e}")
    
    def stop(self):
        """Stop the MQTT client"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT handler stopped")
    
    def publish_message(self, topic: str, payload: str, qos: int = 0) -> bool:
        """Publish a message to the MQTT broker"""
        if not self.is_connected:
            logger.error("Cannot publish message: MQTT client not connected")
            return False
        
        try:
            result = self.client.publish(topic, payload, qos)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published message to {topic}")
                return True
            else:
                logger.error(f"Failed to publish message to {topic}: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False


# Global MQTT handler instance
mqtt_handler = None

def get_mqtt_handler() -> MQTTHandler:
    """Get the global MQTT handler instance"""
    global mqtt_handler
    if mqtt_handler is None:
        mqtt_handler = MQTTHandler()
    return mqtt_handler

def start_mqtt_handler():
    """Start the MQTT handler"""
    handler = get_mqtt_handler()
    handler.start()

def stop_mqtt_handler():
    """Stop the MQTT handler"""
    handler = get_mqtt_handler()
    handler.stop()