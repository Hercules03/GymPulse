#!/usr/bin/env python3
"""
Demo test with limited machines for easy real-time verification
"""
import asyncio
import logging
import signal
import sys
import time
from typing import Dict, List
from pathlib import Path

# Add src to path
sys.path.append('src')
from machine_simulator import MachineSimulator

class DemoTest:
    def __init__(self):
        self.simulators: Dict[str, MachineSimulator] = {}
        self.running = False

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("DemoTest")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, stopping demo...")
        self.stop_all()
        sys.exit(0)

    def create_demo_machines(self):
        """Create 3 demo machines for easy tracking"""

        # Demo machine configurations
        demo_machines = [
            {
                'machineId': 'leg-press-01',
                'name': 'Leg Press Machine 1',
                'category': 'legs',
                'type': 'leg-press',
                'gymId': 'hk-central'
            },
            {
                'machineId': 'bench-press-01',
                'name': 'Bench Press 1',
                'category': 'chest',
                'type': 'bench-press',
                'gymId': 'hk-central'
            },
            {
                'machineId': 'lat-pulldown-01',
                'name': 'Lat Pulldown 1',
                'category': 'back',
                'type': 'lat-pulldown',
                'gymId': 'hk-central'
            }
        ]

        gym_config = {
            'id': 'hk-central',
            'name': 'Central Branch',
            'coordinates': {'lat': 22.2819, 'lon': 114.1577}
        }

        endpoint = "a2udl08tinypzz-ats.iot.ap-east-1.amazonaws.com"

        print("🏗️  Creating demo machines:")
        for machine_config in demo_machines:
            machine_id = machine_config['machineId']

            # Certificate paths
            cert_path = f"certs/{machine_id}.cert.pem"
            key_path = f"certs/{machine_id}.private.key"
            ca_path = "certs/root-CA.crt"

            # Create simulator
            simulator = MachineSimulator(
                machine_config=machine_config,
                gym_config=gym_config,
                cert_path=cert_path,
                key_path=key_path,
                ca_path=ca_path,
                endpoint=endpoint
            )

            # Set callback for state changes
            simulator.on_state_change = self.on_state_change

            self.simulators[machine_id] = simulator
            print(f"   ✅ {machine_id} ({machine_config['category']})")

        print(f"📊 Total demo machines: {len(self.simulators)}")

    def on_state_change(self, machine_id: str, new_state: str, payload: Dict):
        """Callback for state changes - provides user feedback"""
        timestamp = payload.get('timestamp', int(time.time()))
        category = payload.get('category', 'unknown')

        status_emoji = "🔴" if new_state == "occupied" else "🟢"
        print(f"{status_emoji} {machine_id} ({category}) → {new_state.upper()} at {timestamp}")

    async def start_demo(self):
        """Start the demo simulation"""
        if self.running:
            print("⚠️  Demo already running")
            return

        print("\n🚀 Starting Real-Time Demo Test")
        print("=" * 50)
        print("📱 Frontend: http://localhost:3000/")
        print("🔄 Watch for real-time updates in the web interface!")
        print("💡 Machine states will change every 15-30 seconds")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)

        self.running = True

        # Start simulators with staggered delays
        tasks = []
        for i, (machine_id, simulator) in enumerate(self.simulators.items()):
            delay = i * 3  # 3 second delays
            print(f"⏰ Scheduling {machine_id} to start in {delay}s")

            task = asyncio.create_task(self.start_machine_with_delay(simulator, delay))
            tasks.append(task)

        try:
            # Wait for all machines to start
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"❌ Error in demo: {e}")
            self.stop_all()

    async def start_machine_with_delay(self, simulator: MachineSimulator, delay: float):
        """Start a machine with delay"""
        if delay > 0:
            await asyncio.sleep(delay)

        print(f"🔌 Starting {simulator.machine_id}...")
        await simulator.start_simulation()

    def stop_all(self):
        """Stop all simulators"""
        print("\n🛑 Stopping all demo machines...")
        self.running = False

        for machine_id, simulator in self.simulators.items():
            if simulator.running:
                simulator.stop_simulation()
                print(f"   ⏹️  Stopped {machine_id}")

    async def run_demo(self, duration_minutes: int = 5):
        """Run demo for specified duration"""
        print(f"⏱️  Demo will run for {duration_minutes} minutes")

        # Create machines
        self.create_demo_machines()

        # Start demo
        await self.start_demo()

        # Let it run
        print(f"\n⏳ Running demo for {duration_minutes} minutes...")
        print("💻 Open http://localhost:3000/ to see real-time updates!")

        try:
            await asyncio.sleep(duration_minutes * 60)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()

async def main():
    demo = DemoTest()

    try:
        await demo.run_demo(duration_minutes=10)  # 10 minute demo
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        demo.stop_all()

if __name__ == "__main__":
    print("🎬 GymPulse Real-Time Demo Test")
    print("================================")
    asyncio.run(main())