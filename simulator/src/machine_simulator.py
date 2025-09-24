"""
Machine Simulator
Simulates individual gym machine with realistic occupancy patterns
"""
import json
import time
import random
import threading
import logging
import asyncio
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
        self.equipment_type = machine_config.get('type', 'unknown')
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

        # Connection health tracking
        self.publish_failures = 0
        self.max_failures = 5
        self.circuit_open = False
        self.last_success = time.time()

        # Rate limiting
        self.last_publish = 0
        self.min_publish_interval = 2  # Minimum 2 seconds between publishes
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"Machine-{self.machine_id}")
    
    def _setup_mqtt_client(self) -> mqtt5.Client:
        """Setup MQTT5 client with certificates"""
        return mqtt5_client_builder.mtls_from_path(
            endpoint=self.endpoint,
            port=8883,
            cert_filepath=self.cert_path,
            pri_key_filepath=self.key_path,
            ca_filepath=self.ca_path,
            client_id=self.machine_id
        )
    
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
            if connection_future:
                connection_future.result(timeout=30)  # Wait up to 30 seconds
            
            # Give a moment for connection to establish
            import asyncio
            await asyncio.sleep(2)
            
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
        """Publish state change via AWS CLI (more reliable than MQTT SDK)"""
        try:
            # Circuit breaker check
            if self.circuit_open:
                if time.time() - self.last_success < 60:  # 60 second cooldown
                    self.logger.debug(f"Circuit breaker open for {self.machine_id}, skipping publish")
                    return False
                else:
                    self.logger.info(f"Circuit breaker reset for {self.machine_id}, attempting publish")
                    self.circuit_open = False
                    self.publish_failures = 0

            # Rate limiting check
            current_time = time.time()
            if current_time - self.last_publish < self.min_publish_interval:
                wait_time = self.min_publish_interval - (current_time - self.last_publish)
                self.logger.debug(f"Rate limiting {self.machine_id}, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

            # Check for noise injection
            should_inject, noise_type = self.usage_patterns.should_inject_noise()

            if should_inject and noise_type == 'missed_detection':
                self.logger.debug(f"Simulating missed detection for {self.machine_id}")
                return True  # Skip publishing to simulate missed detection

            # Get network delay
            delay = self.usage_patterns.get_network_delay()
            if delay > 0:
                self.logger.debug(f"Simulating {delay}s network delay for {self.machine_id}")
                await asyncio.sleep(delay)

            # Create payload
            payload = self._create_message_payload(new_state)

            # Inject false positive
            if should_inject and noise_type == 'false_positive':
                false_payload = self._create_message_payload(
                    'occupied' if new_state == 'free' else 'free'
                )
                await self._publish_via_aws_cli(false_payload)
                self.logger.debug(f"Injected false positive for {self.machine_id}")
                await asyncio.sleep(random.randint(2, 5))

            # Publish actual state via AWS CLI
            success = await self._publish_via_aws_cli(payload)

            if success:
                self.logger.info(f"Published: {self.machine_id} -> {new_state}")

                # Reset circuit breaker on success
                self.publish_failures = 0
                self.circuit_open = False
                self.last_success = time.time()
                self.last_publish = time.time()

                # Call callback if set
                if self.on_state_change:
                    self.on_state_change(self.machine_id, new_state, payload)

                return True
            else:
                raise Exception("AWS CLI publish failed")

        except Exception as e:
            error_msg = str(e) if str(e) else f"Unknown error: {type(e).__name__}"
            self.logger.error(f"Failed to publish {self.machine_id}: {error_msg}")

            # Circuit breaker logic
            self.publish_failures += 1
            if self.publish_failures >= self.max_failures:
                self.circuit_open = True
                self.logger.warning(f"Circuit breaker opened for {self.machine_id} after {self.publish_failures} failures")

            return False

    async def _publish_via_aws_cli(self, payload: Dict[str, Any]) -> bool:
        """Publish message via AWS CLI"""
        import subprocess
        import base64

        try:
            # Convert payload to base64
            json_payload = json.dumps(payload)
            b64_payload = base64.b64encode(json_payload.encode()).decode()

            # Use AWS CLI to publish
            cmd = [
                "aws", "iot-data", "publish",
                "--topic", self.topic,
                "--payload", b64_payload
            ]

            # Run in thread pool to avoid blocking
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            return True

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.logger.error(f"AWS CLI publish failed for {self.machine_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in AWS CLI publish for {self.machine_id}: {e}")
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
                    await asyncio.sleep(offline_duration)
                    continue
                
                # Get next state transition with Hong Kong 247 Fitness patterns
                next_state, duration = self.usage_patterns.get_realistic_state_transition(
                    self.current_state, current_hour, self.category, self.gym_id, self.equipment_type
                )
                
                # Update state if changed
                if next_state != self.current_state:
                    self._update_state(next_state)
                    await self._publish_state_change(next_state)
                
                # Wait for duration
                self.logger.debug(f"{self.machine_id} waiting {duration}s in {next_state} state")
                await asyncio.sleep(duration)
                
            except Exception as e:
                self.logger.error(f"Error in simulation loop for {self.machine_id}: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def start_simulation(self):
        """Start the machine simulation"""
        if self.running:
            self.logger.warning(f"Simulation already running for {self.machine_id}")
            return

        self.logger.info(f"Starting {self.machine_id} simulation (AWS CLI mode)")
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
                final_publish_request = mqtt5_crt.PublishPacket(
                    topic=self.topic,
                    payload=json.dumps(final_payload).encode('utf-8'),
                    qos=mqtt5_crt.QoS.AT_LEAST_ONCE,
                    retain=True
                )
                self.mqtt_client.publish(final_publish_request)
                
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