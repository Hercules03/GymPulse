import json
import boto3
import time
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
events_table = dynamodb.Table('gym-pulse-events')
aggregates_table = dynamodb.Table('gym-pulse-aggregates')
current_state_table = dynamodb.Table('gym-pulse-current-state')
forecast_table = dynamodb.Table('gym-pulse-forecasts')  # New table for storing forecasts

def lambda_handler(event, context):
    """
    Hourly forecast update Lambda function
    - Runs every hour via EventBridge
    - Compares previous hour's forecast with actual data
    - Updates future forecasts based on accuracy trends
    - Stores forecast data in DynamoDB for tracking
    """

    current_time = datetime.now()
    current_hour = current_time.hour
    previous_hour = (current_hour - 1) % 24

    print(f"Starting hourly forecast update at {current_time.isoformat()}")

    try:
        # Get all machines from current state
        response = current_state_table.scan()
        machines = response['Items']

        forecast_updates = []
        accuracy_metrics = []

        for machine in machines:
            machine_id = machine['machineId']
            gym_id = machine.get('gymId', 'unknown')
            category = machine.get('category', 'unknown')

            print(f"Processing forecast update for {machine_id}")

            # Get actual data from the previous hour
            actual_data = get_actual_usage_for_hour(machine_id, previous_hour)

            # Get the forecast that was made for the previous hour
            previous_forecast = get_previous_forecast(machine_id, previous_hour)

            # Calculate forecast accuracy
            if actual_data and previous_forecast:
                accuracy = calculate_forecast_accuracy(actual_data, previous_forecast)
                accuracy_metrics.append({
                    'machine_id': machine_id,
                    'hour': previous_hour,
                    'actual_usage': actual_data['usage_percentage'],
                    'forecast_usage': previous_forecast['usage_percentage'],
                    'accuracy': accuracy,
                    'timestamp': int(current_time.timestamp())
                })

                print(f"Forecast accuracy for {machine_id} hour {previous_hour}: {accuracy:.2f}%")

            # Generate updated forecasts for remaining hours of today
            updated_forecasts = generate_updated_forecasts(
                machine_id, gym_id, category, current_hour, accuracy_metrics
            )

            # Store updated forecasts in database
            for forecast_data in updated_forecasts:
                store_forecast_in_db(forecast_data)
                forecast_updates.append(forecast_data)

        # Log overall accuracy metrics
        if accuracy_metrics:
            avg_accuracy = sum(m['accuracy'] for m in accuracy_metrics) / len(accuracy_metrics)
            print(f"Average forecast accuracy this hour: {avg_accuracy:.2f}%")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Hourly forecast update completed',
                'machines_updated': len(machines),
                'forecasts_generated': len(forecast_updates),
                'accuracy_metrics': len(accuracy_metrics),
                'timestamp': current_time.isoformat()
            })
        }

    except Exception as e:
        print(f"Error in hourly forecast update: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_actual_usage_for_hour(machine_id, hour):
    """Get actual usage data for a specific machine and hour"""
    try:
        # Query aggregates table for the specific hour
        current_date = datetime.now().date()
        start_of_hour = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
        end_of_hour = start_of_hour + timedelta(hours=1)

        response = aggregates_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('machineId').eq(machine_id) &
                                  boto3.dynamodb.conditions.Key('timestamp15min').between(
                                      int(start_of_hour.timestamp()),
                                      int(end_of_hour.timestamp())
                                  ),
            ScanIndexForward=False,
            Limit=4  # 4 x 15-minute intervals = 1 hour
        )

        if response['Items']:
            # Calculate average usage for the hour
            total_usage = sum(float(item['occupancyRatio']) for item in response['Items'])
            avg_usage = total_usage / len(response['Items'])

            return {
                'machine_id': machine_id,
                'hour': hour,
                'usage_percentage': round(avg_usage, 1),
                'data_points': len(response['Items']),
                'timestamp': int(start_of_hour.timestamp())
            }
    except Exception as e:
        print(f"Error getting actual usage for {machine_id} hour {hour}: {str(e)}")

    return None

def get_previous_forecast(machine_id, hour):
    """Get the forecast that was previously made for this hour"""
    try:
        current_date = datetime.now().date()
        forecast_key = f"{machine_id}_{current_date.isoformat()}_{hour:02d}"

        response = forecast_table.get_item(
            Key={'forecast_id': forecast_key}
        )

        if 'Item' in response:
            return response['Item']
    except Exception as e:
        print(f"Error getting previous forecast for {machine_id} hour {hour}: {str(e)}")

    return None

def calculate_forecast_accuracy(actual_data, forecast_data):
    """Calculate forecast accuracy as percentage"""
    actual_usage = actual_data['usage_percentage']
    forecast_usage = float(forecast_data['usage_percentage'])

    # Calculate absolute percentage error
    error = abs(actual_usage - forecast_usage)
    accuracy = max(0, 100 - error)  # Convert error to accuracy percentage

    return accuracy

def generate_updated_forecasts(machine_id, gym_id, category, current_hour, accuracy_metrics):
    """Generate updated forecasts for remaining hours incorporating recent accuracy"""
    forecasts = []

    try:
        # Get historical data for baseline patterns
        end_time = int(time.time())
        start_time = end_time - (20 * 24 * 60 * 60)  # 20 days of data

        response = aggregates_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('machineId').eq(machine_id) &
                                  boto3.dynamodb.conditions.Key('timestamp15min').between(start_time, end_time),
            ScanIndexForward=False
        )

        # Process historical data by hour
        hourly_data = {}
        for record in response['Items']:
            timestamp = int(record['timestamp15min'])
            hour = datetime.fromtimestamp(timestamp).hour
            occupancy_ratio = float(record.get('occupancyRatio', 0))

            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(occupancy_ratio)

        # Calculate trend adjustment based on recent accuracy
        trend_adjustment = calculate_trend_adjustment(machine_id, accuracy_metrics)

        # Generate forecasts for remaining hours
        current_date = datetime.now().date()
        for hour in range(current_hour + 1, 24):  # Only future hours
            if hour in hourly_data:
                # Base forecast on historical average
                historical_avg = sum(hourly_data[hour]) / len(hourly_data[hour])

                # Apply trend adjustment based on recent accuracy
                adjusted_forecast = historical_avg * trend_adjustment
                adjusted_forecast = max(5.0, min(95.0, adjusted_forecast))  # Clamp to reasonable range

                forecast_data = {
                    'forecast_id': f"{machine_id}_{current_date.isoformat()}_{hour:02d}",
                    'machine_id': machine_id,
                    'gym_id': gym_id,
                    'category': category,
                    'forecast_hour': hour,
                    'usage_percentage': Decimal(str(round(adjusted_forecast, 1))),
                    'confidence': 'medium',
                    'trend_adjustment': Decimal(str(round(trend_adjustment, 3))),
                    'historical_samples': len(hourly_data[hour]),
                    'created_at': int(datetime.now().timestamp()),
                    'forecast_date': current_date.isoformat()
                }

                forecasts.append(forecast_data)

        print(f"Generated {len(forecasts)} updated forecasts for {machine_id}")

    except Exception as e:
        print(f"Error generating updated forecasts for {machine_id}: {str(e)}")

    return forecasts

def calculate_trend_adjustment(machine_id, accuracy_metrics):
    """Calculate trend adjustment factor based on recent forecast accuracy"""

    # Find accuracy metrics for this machine
    machine_metrics = [m for m in accuracy_metrics if m['machine_id'] == machine_id]

    if not machine_metrics:
        return 1.0  # No adjustment if no recent data

    # Calculate average accuracy for this machine
    avg_accuracy = sum(m['accuracy'] for m in machine_metrics) / len(machine_metrics)

    # Adjust trend based on accuracy
    if avg_accuracy > 80:  # High accuracy
        return 1.0  # No adjustment needed
    elif avg_accuracy > 60:  # Medium accuracy
        return 0.95  # Slight conservative adjustment
    else:  # Low accuracy
        return 0.9  # More conservative adjustment

def store_forecast_in_db(forecast_data):
    """Store forecast data in DynamoDB"""
    try:
        forecast_table.put_item(Item=forecast_data)
        print(f"Stored forecast: {forecast_data['forecast_id']}")
    except Exception as e:
        print(f"Error storing forecast {forecast_data['forecast_id']}: {str(e)}")