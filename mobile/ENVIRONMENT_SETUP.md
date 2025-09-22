# GymPulse Mobile App - Environment Configuration

## Overview
This document outlines the environment configuration setup for the GymPulse Flutter mobile application, ensuring proper connectivity to the backend services.

## Environment Variables

### API Configuration
- **API_BASE_URL**: `https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod`
- **WEBSOCKET_URL**: `wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod`

### Google Maps Integration
- **GOOGLE_MAPS_API_KEY**: Your Google Maps API key for location services and maps

### Firebase Configuration (Optional)
- **FIREBASE_PROJECT_ID**: Firebase project ID for push notifications
- **FIREBASE_MESSAGING_SENDER_ID**: Firebase messaging sender ID

### App Configuration
- **APP_NAME**: `GymPulse`
- **APP_VERSION**: `1.0.0`
- **DEBUG_MODE**: `true` (for development)

### Feature Flags
- **ENABLE_ANALYTICS**: `true`
- **ENABLE_PUSH_NOTIFICATIONS**: `true`
- **ENABLE_LOCATION_SERVICES**: `true`
- **ENABLE_WEBSOCKET**: `true`

## Files Updated

### 1. `.env` File
Created with all necessary environment variables and their default values.

### 2. `lib/core/config/environment_config.dart`
- Centralized environment configuration management
- Loads variables from `.env` file with fallback defaults
- Provides type-safe access to configuration values
- Includes debugging utilities

### 3. Updated Services
- **API Client** (`lib/core/network/api_client.dart`): Now uses `EnvironmentConfig.apiBaseUrl`
- **WebSocket Service** (`lib/core/network/websocket_service.dart`): Now uses `EnvironmentConfig.websocketUrl`
- **Main App** (`lib/main.dart`): Initializes environment configuration on startup

### 4. Constants Updated
- **API Constants** (`lib/core/constants/api_constants.dart`): Updated with correct URLs
- **WebSocket Constants** (`lib/core/constants/websocket_constants.dart`): Updated with correct WebSocket URL
- **App Constants** (`lib/core/constants/app_constants.dart`): Updated with correct URLs

## Backend API Endpoints

The app connects to the following AWS API Gateway endpoints:

### REST API
- **Base URL**: `https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod`
- **Branches**: `GET /branches`
- **Machines**: `GET /branches/{branchId}/categories/{category}/machines`
- **Machine History**: `GET /machines/{machineId}/history`
- **Alerts**: `POST /alerts`, `GET /alerts`, `DELETE /alerts/{alertId}`
- **Chat**: `POST /chat`
- **Health Check**: `GET /health`

### WebSocket API
- **WebSocket URL**: `wss://f33iwzqgcd.execute-api.ap-east-1.amazonaws.com/prod`
- **Real-time Updates**: Machine status updates, user alerts
- **Connection Management**: Automatic reconnection, ping/pong heartbeat

## Configuration Verification

### Debug Information
The app includes a debug widget (`EnvironmentInfoWidget`) that displays current configuration values. This can be accessed through the Settings page.

### Settings Page
The Settings page now shows:
- Current environment configuration
- App settings toggles
- Feature flags status

## Development vs Production

### Development
- Uses `.env` file for local configuration
- Debug mode enabled
- Detailed logging
- Mock data fallbacks

### Production
- Environment variables should be set at the system level
- Debug mode disabled
- Minimal logging
- Real API endpoints only

## Next Steps

1. **Google Maps Setup**: Add your Google Maps API key to the `.env` file
2. **Firebase Setup**: Configure Firebase for push notifications (optional)
3. **Testing**: Verify all API endpoints are accessible
4. **WebSocket Testing**: Test real-time connectivity
5. **Environment Variables**: Set production environment variables for deployment

## Troubleshooting

### Common Issues
1. **API Connection Failed**: Check if the API Gateway URL is correct and accessible
2. **WebSocket Connection Failed**: Verify WebSocket URL and network connectivity
3. **Environment Variables Not Loading**: Ensure `.env` file is in the correct location
4. **Google Maps Not Working**: Verify API key is valid and has proper permissions

### Debug Commands
```bash
# Check environment configuration
flutter run --debug

# View logs
flutter logs

# Test API connectivity
curl https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod/health
```

## Security Notes

- Never commit `.env` files to version control
- Use environment variables in production
- Rotate API keys regularly
- Implement proper authentication for production use
