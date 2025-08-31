"""
Gym Simulator Coordinator
Manages multiple machine simulators across gym branches
"""
import json
import asyncio
import logging
import signal
import sys
from typing import Dict, List, Any
from pathlib import Path

from machine_simulator import MachineSimulator
from usage_patterns import UsagePatterns


class GymSimulator:
    def __init__(self, config_path: str = "config/machines.json", 
                 cert_dir: str = "certs", endpoint: str = None):
        """Initialize gym simulator coordinator"""
        self.config_path = config_path
        self.cert_dir = Path(cert_dir)
        self.endpoint = endpoint or self._get_iot_endpoint()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.machines: Dict[str, MachineSimulator] = {}
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('simulator.log')
            ]
        )
        self.logger = logging.getLogger("GymSimulator")
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _get_iot_endpoint(self) -> str:
        """Get IoT endpoint from environment or AWS CLI"""
        import os
        import subprocess
        
        # Try environment variable first
        endpoint = os.getenv('IOT_ENDPOINT')
        if endpoint:
            return endpoint
        
        try:
            # Try AWS CLI
            result = subprocess.run([
                'aws', 'iot', 'describe-endpoint', 
                '--endpoint-type', 'iot:Data-ATS'
            ], capture_output=True, text=True, check=True)
            
            endpoint_data = json.loads(result.stdout)
            return endpoint_data['endpointAddress']
            
        except Exception as e:
            self.logger.error(f"Failed to get IoT endpoint: {e}")
            raise ValueError("Could not determine IoT endpoint. Set IOT_ENDPOINT environment variable.")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop_all_simulations())
    
    def _get_machine_certificates(self, machine_id: str) -> Dict[str, str]:
        """Get certificate paths for a machine"""
        return {
            'cert_path': str(self.cert_dir / f"{machine_id}.cert.pem"),
            'key_path': str(self.cert_dir / f"{machine_id}.private.key"),
            'ca_path': str(self.cert_dir / "root-CA.crt")
        }
    
    def create_machine_simulators(self):
        """Create all machine simulators from configuration"""
        self.logger.info("Creating machine simulators...")
        
        for branch in self.config['branches']:
            branch_id = branch['id']
            
            for machine_config in branch['machines']:
                machine_id = machine_config['machineId']
                
                # Get certificates for this machine
                certs = self._get_machine_certificates(machine_id)
                
                # Create simulator
                simulator = MachineSimulator(
                    machine_config=machine_config,
                    gym_config=branch,
                    endpoint=self.endpoint,
                    **certs
                )
                
                # Set callback for state changes
                simulator.on_state_change = self._on_machine_state_change
                
                self.machines[machine_id] = simulator
                
                self.logger.info(f"Created simulator for {machine_id} at {branch_id}")
        
        self.logger.info(f"Created {len(self.machines)} machine simulators")
    
    def _on_machine_state_change(self, machine_id: str, new_state: str, payload: Dict[str, Any]):
        """Callback for when machine state changes"""
        self.logger.debug(f"State change: {machine_id} -> {new_state}")
        
        # Could add additional logging, metrics, or notifications here
        
    async def start_simulation(self, machine_ids: List[str] = None):
        """Start simulation for specified machines (or all machines)"""
        if self.running:
            self.logger.warning("Simulation already running")
            return
        
        if not self.machines:
            self.create_machine_simulators()
        
        # Determine which machines to start
        machines_to_start = machine_ids or list(self.machines.keys())
        
        self.logger.info(f"Starting simulation for {len(machines_to_start)} machines...")
        
        self.running = True
        
        # Start all machine simulations concurrently
        tasks = []
        for machine_id in machines_to_start:
            if machine_id in self.machines:
                task = asyncio.create_task(
                    self.machines[machine_id].start_simulation()
                )
                tasks.append(task)
                self.logger.info(f"Started simulation for {machine_id}")
        
        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
            await self.stop_all_simulations()
        except Exception as e:
            self.logger.error(f"Error in simulation: {e}")
            await self.stop_all_simulations()
    
    async def stop_all_simulations(self):
        """Stop all running simulations"""
        self.logger.info("Stopping all simulations...")
        
        self.running = False
        
        # Stop all machines
        stop_tasks = []
        for machine_id, simulator in self.machines.items():
            if simulator.running:
                stop_tasks.append(
                    asyncio.create_task(asyncio.to_thread(simulator.stop_simulation))
                )
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self.logger.info("All simulations stopped")
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get status of all simulations"""
        status = {
            'running': self.running,
            'total_machines': len(self.machines),
            'machines': {}
        }
        
        for machine_id, simulator in self.machines.items():
            status['machines'][machine_id] = simulator.get_status()
        
        return status
    
    async def run_demo_scenario(self, duration_minutes: int = 10):
        """Run a specific demo scenario with controlled state changes"""
        self.logger.info(f"Starting demo scenario for {duration_minutes} minutes...")
        
        # Start simulation
        await self.start_simulation()
        
        # Let it run for the specified duration
        await asyncio.sleep(duration_minutes * 60)
        
        # Stop simulation
        await self.stop_all_simulations()
        
        self.logger.info("Demo scenario completed")
    
    def create_test_certificates(self):
        """Create test certificates for development (NOT for production)"""
        self.logger.warning("Creating test certificates - NOT for production use!")
        
        cert_dir = Path(self.cert_dir)
        cert_dir.mkdir(exist_ok=True)
        
        # This would typically involve AWS IoT certificate creation
        # For now, create placeholder files to show structure
        
        for machine_id in [m['machineId'] for branch in self.config['branches'] 
                          for m in branch['machines']]:
            
            cert_file = cert_dir / f"{machine_id}.cert.pem"
            key_file = cert_dir / f"{machine_id}.private.key"
            
            if not cert_file.exists():
                cert_file.write_text(f"# Test certificate for {machine_id}\n# Replace with actual certificate")
                self.logger.info(f"Created placeholder cert: {cert_file}")
            
            if not key_file.exists():
                key_file.write_text(f"# Test private key for {machine_id}\n# Replace with actual private key")
                self.logger.info(f"Created placeholder key: {key_file}")
        
        # Create root CA placeholder
        ca_file = cert_dir / "root-CA.crt"
        if not ca_file.exists():
            ca_file.write_text("# Root CA certificate\n# Replace with actual root CA")
            self.logger.info(f"Created placeholder CA: {ca_file}")


async def main():
    """Main entry point"""
    simulator = GymSimulator()
    
    try:
        # Create test certificates for development
        simulator.create_test_certificates()
        
        # Run demo scenario
        await simulator.run_demo_scenario(duration_minutes=5)
        
    except Exception as e:
        logging.error(f"Simulation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))