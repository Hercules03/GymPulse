#!/bin/bash

# Script to set up Google Maps API key for iOS
# This script reads the GOOGLE_MAPS_API_KEY from .env file and updates the Info.plist

echo "🔧 Setting up Google Maps API key for iOS..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please make sure you have a .env file with GOOGLE_MAPS_API_KEY"
    exit 1
fi

# Read API key from .env file
API_KEY=$(grep "GOOGLE_MAPS_API_KEY=" .env | cut -d '=' -f2)

if [ -z "$API_KEY" ]; then
    echo "❌ Error: GOOGLE_MAPS_API_KEY not found in .env file"
    echo "Please add GOOGLE_MAPS_API_KEY=your_api_key_here to your .env file"
    exit 1
fi

echo "✅ Found Google Maps API key in .env file"

# Update Info.plist with the API key
INFO_PLIST="ios/Runner/Info.plist"

if [ -f "$INFO_PLIST" ]; then
    # Use sed to replace the placeholder with the actual API key
    sed -i '' "s/YOUR_GOOGLE_MAPS_API_KEY_HERE/$API_KEY/g" "$INFO_PLIST"
    echo "✅ Updated Info.plist with Google Maps API key"
else
    echo "❌ Error: Info.plist not found at $INFO_PLIST"
    exit 1
fi

echo "🎉 Google Maps setup complete!"
echo "You can now run: flutter run"

