#!/usr/bin/env python3
"""
GymPulse Device Simulator
Main entry point for the gym equipment IoT simulator
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gym_simulator import GymSimulator


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='GymPulse IoT Device Simulator')
    parser.add_argument('--config', '-c', default='config/machines.json',
                       help='Configuration file path')
    parser.add_argument('--cert-dir', default='certs',
                       help='Certificate directory path')
    parser.add_argument('--endpoint', 
                       help='AWS IoT endpoint (or set IOT_ENDPOINT env var)')
    parser.add_argument('--duration', '-d', type=int, default=60,
                       help='Simulation duration in minutes')
    parser.add_argument('--machines', nargs='+',
                       help='Specific machine IDs to simulate')
    parser.add_argument('--demo', action='store_true',
                       help='Run demo scenario')
    parser.add_argument('--create-certs', action='store_true',
                       help='Create test certificate placeholders')
    parser.add_argument('--status', action='store_true',
                       help='Show simulation status')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    try:
        # Create simulator
        simulator = GymSimulator(
            config_path=args.config,
            cert_dir=args.cert_dir,
            endpoint=args.endpoint
        )
        
        if args.create_certs:
            simulator.create_test_certificates()
            print("✅ Test certificate placeholders created")
            return 0
        
        if args.demo:
            print(f"🚀 Starting demo scenario for {args.duration} minutes...")
            await simulator.run_demo_scenario(args.duration)
            
        elif args.status:
            status = simulator.get_simulation_status()
            print("📊 Simulation Status:")
            print(f"  Running: {status['running']}")
            print(f"  Total machines: {status['total_machines']}")
            
        else:
            print(f"🏋️ Starting GymPulse simulator for {args.duration} minutes...")
            print(f"📍 Machines: {len(args.machines) if args.machines else 'all'}")
            
            # Start simulation
            await simulator.start_simulation(args.machines)
            
            # Run for specified duration
            await asyncio.sleep(args.duration * 60)
            
            # Stop simulation
            await simulator.stop_all_simulations()
        
        print("✅ Simulation completed successfully")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return 130
        
    except Exception as e:
        logging.error(f"❌ Simulation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
