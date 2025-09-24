"""
Forecast Integration for API Handlers

Integrates the new seasonality-based forecasting with existing API endpoints.
"""
import os
import sys
from datetime import datetime

# Add forecast module to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'forecast'))

try:
    from threshold_tuner import ThresholdTuner
    from seasonality_model import SeasonalityModel
    from data_processor import HistoricalDataProcessor
    FORECAST_AVAILABLE = True
except ImportError as e:
    print(f"Forecast modules not available: {e}")
    FORECAST_AVAILABLE = False


class ForecastIntegration:
    """Integrates forecasting with API responses"""
    
    def __init__(self):
        if FORECAST_AVAILABLE:
            self.threshold_tuner = ThresholdTuner()
            self.seasonality_model = SeasonalityModel()
        else:
            self.threshold_tuner = None
            self.seasonality_model = None
    
    def get_enhanced_machine_forecast(self, machine_id: str) -> dict:
        """
        Get enhanced forecast for machine using seasonality model
        
        Args:
            machine_id: Machine to forecast
            
        Returns:
            Enhanced forecast dict with display information
        """
        if not FORECAST_AVAILABLE or not self.threshold_tuner:
            return self.get_simple_forecast_fallback(machine_id)
        
        try:
            # Get display-ready forecast
            forecast_result = self.threshold_tuner.get_machine_forecast_display(
                machine_id, datetime.utcnow()
            )
            
            if 'error' in forecast_result:
                return self.get_simple_forecast_fallback(machine_id)
            
            forecast = forecast_result['forecast']
            raw_prediction = forecast_result.get('raw_prediction', {})
            
            # Convert to API response format
            return {
                'likelyFreeIn30m': forecast['classification'] == 'likely_free',
                'classification': forecast['classification'],
                'display_text': forecast['display_text'],
                'color': forecast['color'],
                'confidence': forecast['confidence_level'],
                'confidence_text': forecast.get('confidence_text', ''),
                'show_to_user': forecast['show_to_user'],
                'metadata': {
                    'probability': raw_prediction.get('probability', 0.5),
                    'sample_size': raw_prediction.get('sample_size', 0),
                    'forecast_time': raw_prediction.get('forecast_time'),
                    'reliable': raw_prediction.get('reliable', False)
                },
                'reason': f"Based on {raw_prediction.get('sample_size', 0)} historical samples"
            }
            
        except Exception as e:
            print(f"Enhanced forecast failed for {machine_id}: {str(e)}")
            return self.get_simple_forecast_fallback(machine_id)
    
    def get_category_forecast(self, gym_id: str, category: str) -> dict:
        """
        Get forecast for entire category
        
        Args:
            gym_id: Gym branch ID
            category: Equipment category
            
        Returns:
            Category forecast dict
        """
        if not FORECAST_AVAILABLE or not self.seasonality_model:
            return {
                'classification': 'unavailable',
                'display_text': 'Forecast unavailable',
                'reason': 'Forecasting system not available'
            }
        
        try:
            forecast_result = self.seasonality_model.get_category_forecast(
                gym_id, category, datetime.utcnow(), forecast_minutes=30
            )
            
            if 'error' in forecast_result:
                return {
                    'classification': 'error',
                    'display_text': 'Forecast error',
                    'reason': forecast_result['error']
                }
            
            forecast_data = forecast_result['forecast']
            
            # Classify using threshold tuner
            if self.threshold_tuner and forecast_data.get('reliable'):
                classification = self.threshold_tuner.classify_availability_forecast(
                    forecast_data['probability'],
                    forecast_data['confidence'],
                    forecast_data['sample_size']
                )
                
                return {
                    'classification': classification['classification'],
                    'display_text': classification['display_text'],
                    'color': classification['color'],
                    'confidence': classification['confidence_level'],
                    'show_to_user': classification['show_to_user'],
                    'metadata': classification['metadata']
                }
            else:
                return {
                    'classification': 'insufficient_data',
                    'display_text': 'Insufficient data',
                    'reason': f"Only {forecast_data.get('sample_size', 0)} samples available"
                }
                
        except Exception as e:
            print(f"Category forecast failed for {gym_id}/{category}: {str(e)}")
            return {
                'classification': 'error',
                'display_text': 'Forecast unavailable',
                'reason': str(e)
            }
    
    def enhance_machine_response(self, machine_data: dict) -> dict:
        """
        Enhance machine data with forecast information
        
        Args:
            machine_data: Machine data dict from current_state
            
        Returns:
            Enhanced machine data with forecast
        """
        machine_id = machine_data.get('machineId')
        if not machine_id:
            return machine_data
        
        # Add forecast data
        forecast = self.get_enhanced_machine_forecast(machine_id)
        machine_data['forecast'] = forecast
        
        return machine_data
    
    def enhance_machines_list(self, machines: list) -> list:
        """
        Enhance list of machines with forecast data
        
        Args:
            machines: List of machine dicts
            
        Returns:
            Enhanced machines list with forecasts
        """
        enhanced_machines = []
        
        for machine in machines:
            enhanced_machine = self.enhance_machine_response(machine)
            enhanced_machines.append(enhanced_machine)
        
        return enhanced_machines
    
    def get_simple_forecast_fallback(self, machine_id: str) -> dict:
        """
        Simple forecast fallback when enhanced forecasting unavailable
        
        Args:
            machine_id: Machine to forecast
            
        Returns:
            Simple forecast dict
        """
        # This is the original simple forecast logic
        return {
            'likelyFreeIn30m': False,
            'classification': 'unavailable',
            'display_text': 'Forecast unavailable',
            'color': 'gray',
            'confidence': 'none',
            'show_to_user': False,
            'reason': 'Enhanced forecasting system not available',
            'metadata': {
                'probability': 0.5,
                'sample_size': 0,
                'reliable': False
            }
        }


# Global instance for use in API handlers
forecast_integration = ForecastIntegration()


def get_enhanced_forecast(machine_id: str) -> dict:
    """
    Get enhanced forecast for machine - function for backward compatibility
    
    Args:
        machine_id: Machine to forecast
        
    Returns:
        Enhanced forecast dict
    """
    return forecast_integration.get_enhanced_machine_forecast(machine_id)


def enhance_machines_with_forecasts(machines: list) -> list:
    """
    Enhance machines list with forecasts - function for backward compatibility
    
    Args:
        machines: List of machine dicts
        
    Returns:
        Enhanced machines list
    """
    return forecast_integration.enhance_machines_list(machines)


def get_category_forecast_summary(gym_id: str, category: str) -> dict:
    """
    Get category forecast summary - function for backward compatibility
    
    Args:
        gym_id: Gym branch ID
        category: Equipment category
        
    Returns:
        Category forecast dict
    """
    return forecast_integration.get_category_forecast(gym_id, category)