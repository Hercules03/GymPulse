#!/usr/bin/env python3
"""
Automated script to generate training data - fast version (no cleanup)
"""
import sys
sys.path.append('.')

from generate_training_data import TrainingDataGenerator
import time

def main():
    """Run training data generation automatically - skip cleanup"""
    print("🚀 Starting fast training data generation (tables already clean)...")

    # Initialize generator
    generator = TrainingDataGenerator()

    print(f"📊 {len(generator.machines)} machines across {len(generator.config['branches'])} branches")

    # Configuration - skip cleanup since we just recreated tables
    cleanup = False  # Skip cleanup
    days = 365
    workers = 16

    print(f"📋 Configuration:")
    print(f"   - Cleanup existing data: No (already done)")
    print(f"   - Generate {days} days of data")
    print(f"   - For {len(generator.machines)} machines")
    print(f"   - Total: {days * len(generator.machines)} machine-days")
    print(f"   - Using {workers} parallel workers")

    start_time = time.time()

    # Generate new realistic data directly (no cleanup)
    print(f"\n📈 Generating {days} days of training data...")
    generator.generate_training_data(days=days, max_workers=workers)

    duration = time.time() - start_time

    print(f"\n✅ Complete! Generated training data in {duration:.1f} seconds")
    print("🧠 Your ML forecasting should now have realistic data to learn from!")
    print("\n🔄 Next steps:")
    print("   1. Restart your ML forecasting Lambda to pick up new data")
    print("   2. Check machine detail pages - heatmaps should now be different per machine")
    print("   3. Verify peak hours now match realistic patterns (Evening: 18-22, not 1-4 AM)")

if __name__ == "__main__":
    main()