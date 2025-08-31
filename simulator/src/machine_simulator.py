"""
Machine Simulator
Simulates individual gym machine with realistic occupancy patterns
"""
import json
import time
import random
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Optional
from awsiot import mqtt5_client_builder, mqtt5
from awscrt import mqtt5 as mqtt5_crt
from concurrent.futures import Future

from usage_patterns import UsagePatterns


class MachineSimulator:
    def __init__(self, machine_config: Dict[str, Any], gym_config: Dict[str, Any], 
                 cert_path: str, key_path: str, ca_path: str, endpoint: str):
        """Initialize machine simulator with configuration"""
        self.machine_id = machine_config['machineId']
        self.gym_id = gym_config['id']
        self.category = machine_config['category']
        self.machine_name = machine_config['name']
        self.coordinates = gym_config['coordinates']
        
        # MQTT configuration
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path  
        self.ca_path = ca_path
        self.topic = f"org/{self.gym_id}/machines/{self.machine_id}/status"
        
        # State management
        self.current_state = 'free'
        self.state_start_time = time.time()
        self.running = False
        self.mqtt_client = None
        self.usage_patterns = UsagePatterns()
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"Machine-{self.machine_id}")
    
    def _setup_mqtt_client(self) -> mqtt5.Client:
        """Setup MQTT5 client with certificates"""
        client_bootstrap = mqtt5_client_builder.mtls_from_path(
            endpoint=self.endpoint,
            port=8883,
            cert_filepath=self.cert_path,
            pri_key_filepath=self.key_path,
            ca_filepath=self.ca_path,
            client_id=self.machine_id
        )
        
        # Configure client options
        client_options = mqtt5_crt.ClientOptions(
            host_name=self.endpoint,
            port=8883,
            client_id=self.machine_id,
            keep_alive_interval_seconds=30,
        )
        
        return mqtt5.Client(client_bootstrap, client_options)
    
    def _on_connection_success(self, connection, callback_data):
        """Called when MQTT connection succeeds"""
        self.logger.info(f"Connected to AWS IoT Core: {self.machine_id}")
    
    def _on_connection_failure(self, connection, callback_data):
        """Called when MQTT connection fails"""
        self.logger.error(f"Connection failed for {self.machine_id}: {callback_data}")
    
    def _on_disconnect(self, disconnect_data):
        """Called when MQTT disconnects"""
        self.logger.warning(f"Disconnected: {self.machine_id}")
    
    async def connect(self) -> bool:
        """Connect to AWS IoT Core"""
        try:
            self.mqtt_client = self._setup_mqtt_client()
            
            # Set callbacks
            self.mqtt_client.on_connection_success = self._on_connection_success
            self.mqtt_client.on_connection_failure = self._on_connection_failure
            self.mqtt_client.on_disconnection = self._on_disconnect
            
            # Connect
            connection_future = self.mqtt_client.start()
            connection_future.result(timeout=30)  # Wait up to 30 seconds
            
            self.logger.info(f"Machine {self.machine_id} connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect {self.machine_id}: {str(e)}")
            return False
    
    def _create_message_payload(self, status: str, timestamp: Optional[float] = None) -> Dict[str, Any]:
        """Create MQTT message payload"""
        if timestamp is None:
            timestamp = time.time()
        
        return {
            'machineId': self.machine_id,
            'gymId': self.gym_id,
            'status': status,
            'timestamp': int(timestamp),
            'category': self.category,
            'coordinates': self.coordinates,
            'machine_name': self.machine_name
        }
    
    async def _publish_state_change(self, new_state: str, retain: bool = True):
        """Publish state change to MQTT topic"""
        if not self.mqtt_client:
            self.logger.error("MQTT client not connected")
            return False
        
        try:
            # Check for noise injection
            should_inject, noise_type = self.usage_patterns.should_inject_noise()
            
            if should_inject and noise_type == 'missed_detection':
                self.logger.debug(f"Simulating missed detection for {self.machine_id}")
                return True  # Skip publishing to simulate missed detection
            
            # Get network delay
            delay = self.usage_patterns.get_network_delay()
            if delay > 0:
                self.logger.debug(f"Simulating {delay}s network delay for {self.machine_id}")
                time.sleep(delay)
            
            # Create payload
            payload = self._create_message_payload(new_state)
            
            # Inject false positive
            if should_inject and noise_type == 'false_positive':
                # Send opposite state briefly then correct state
                false_payload = self._create_message_payload(
                    'occupied' if new_state == 'free' else 'free'
                )
                
                publish_future = self.mqtt_client.publish(
                    topic=self.topic,
                    payload=json.dumps(false_payload),
                    qos=mqtt5_crt.QoS.AT_LEAST_ONCE,
                    retain=retain
                )
                publish_future.result(timeout=10)
                
                self.logger.debug(f"Injected false positive for {self.machine_id}")
                
                # Brief delay then send correct state
                time.sleep(random.randint(2, 5))
            
            # Publish actual state
            publish_future = self.mqtt_client.publish(
                topic=self.topic,
                payload=json.dumps(payload),
                qos=mqtt5_crt.QoS.AT_LEAST_ONCE,
                retain=retain
            )
            
            publish_future.result(timeout=10)
            
            self.logger.info(f"Published: {self.machine_id} -> {new_state}")
            
            # Call callback if set
            if self.on_state_change:
                self.on_state_change(self.machine_id, new_state, payload)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to publish {self.machine_id}: {str(e)}")
            return False
    
    def _update_state(self, new_state: str):
        """Update internal state"""
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        self.logger.debug(f"{self.machine_id}: {old_state} -> {new_state}")
    
    async def _simulation_loop(self):
        """Main simulation loop"""
        self.logger.info(f"Starting simulation loop for {self.machine_id}")
        
        while self.running:
            try:
                current_hour = datetime.now().hour
                
                # Check if device should go offline
                if self.usage_patterns.should_go_offline():
                    offline_duration = random.randint(120, 300)  # 2-5 minutes
                    self.logger.info(f"{self.machine_id} going offline for {offline_duration}s")
                    time.sleep(offline_duration)
                    continue
                
                # Get next state transition
                next_state, duration = self.usage_patterns.get_realistic_state_transition(
                    self.current_state, current_hour, self.category
                )
                
                # Update state if changed
                if next_state != self.current_state:
                    self._update_state(next_state)
                    await self._publish_state_change(next_state)
                
                # Wait for duration
                self.logger.debug(f"{self.machine_id} waiting {duration}s in {next_state} state")
                time.sleep(duration)
                
            except Exception as e:
                self.logger.error(f"Error in simulation loop for {self.machine_id}: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    async def start_simulation(self):
        """Start the machine simulation"""
        if self.running:
            self.logger.warning(f"Simulation already running for {self.machine_id}")
            return
        
        # Connect to MQTT
        if not await self.connect():
            self.logger.error(f"Failed to connect {self.machine_id}")
            return
        
        self.running = True
        
        # Publish initial state
        await self._publish_state_change(self.current_state)
        
        # Start simulation loop
        await self._simulation_loop()
    
    def stop_simulation(self):
        """Stop the machine simulation"""
        self.logger.info(f"Stopping simulation for {self.machine_id}")
        self.running = False
        
        if self.mqtt_client:
            try:
                # Publish final state
                final_payload = self._create_message_payload('offline')
                self.mqtt_client.publish(
                    topic=self.topic,
                    payload=json.dumps(final_payload),
                    qos=mqtt5_crt.QoS.AT_LEAST_ONCE,
                    retain=True
                )
                
                # Disconnect
                self.mqtt_client.stop()
                self.logger.info(f"Disconnected {self.machine_id}")
                
            except Exception as e:
                self.logger.error(f"Error stopping {self.machine_id}: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current machine status"""
        return {
            'machine_id': self.machine_id,
            'gym_id': self.gym_id,
            'category': self.category,
            'current_state': self.current_state,
            'state_duration': time.time() - self.state_start_time,
            'running': self.running,
            'connected': self.mqtt_client is not None
        }