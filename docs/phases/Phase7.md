# Phase 7: Forecasting Chip (Baseline) - Step-by-Step Breakdown

## Overview
Implement baseline weekly seasonality forecasting to show "likely free in 30m" predictions on machine tiles and chatbot responses.

## Prerequisites
- Phase 3 aggregation pipeline operational
- Historical data available in aggregates table
- Frontend tiles ready for forecast integration

---

## Step 1: Historical Occupancy Analysis
**Duration**: 30 minutes  
**Status**: ✅ Completed

### 1.1 Data Collection and Preparation
- [x] **File**: `lambda/forecast/data_processor.py` - ✅ Implemented
- [x] Query aggregates table for historical 15-minute bins
- [x] Collect at least 2 weeks of data per machine/category
- [x] Handle missing data points and gaps
- [x] Structure data by weekday and time slot

### 1.2 Occupancy Pattern Analysis
```python
def analyze_occupancy_patterns(machine_id, historical_data):
    """
    Analyze historical occupancy patterns for forecasting
    """
    patterns = {}
    
    for record in historical_data:
        weekday = record['timestamp'].weekday()  # 0=Monday, 6=Sunday
        hour = record['timestamp'].hour
        minute_slot = (record['timestamp'].minute // 15) * 15  # 0, 15, 30, 45
        
        time_key = f"{weekday}_{hour:02d}_{minute_slot:02d}"
        
        if time_key not in patterns:
            patterns[time_key] = []
        
        patterns[time_key].append(record['occupancyRatio'])
    
    return patterns
```

### 1.3 Data Quality Assessment
- [x] Identify machines with insufficient data
- [x] Handle seasonal variations and anomalies
- [x] Validate data consistency across time periods

---

## Step 2: Weekly Seasonality Calculation
**Duration**: 35 minutes  
**Status**: ✅ Completed

### 2.1 Seasonality Model Implementation
- [x] **File**: `lambda/forecast/seasonality_model.py` - ✅ Implemented
- [x] Calculate average occupancy by weekday/hour/15min slot
- [x] Compute standard deviation for confidence intervals
- [x] Generate baseline weekly pattern per machine

### 2.2 Probability Calculation
```python
def calculate_free_probability(patterns, current_time, forecast_minutes=30):
    """
    Calculate probability machine will be free in specified minutes
    """
    target_time = current_time + timedelta(minutes=forecast_minutes)
    weekday = target_time.weekday()
    hour = target_time.hour
    minute_slot = (target_time.minute // 15) * 15
    
    time_key = f"{weekday}_{hour:02d}_{minute_slot:02d}"
    
    if time_key in patterns:
        occupancy_history = patterns[time_key]
        avg_occupancy = sum(occupancy_history) / len(occupancy_history)
        free_probability = 1.0 - (avg_occupancy / 100.0)  # Convert to probability
        
        return {
            'probability': free_probability,
            'confidence': calculate_confidence(occupancy_history),
            'sample_size': len(occupancy_history)
        }
    
    return {'probability': 0.5, 'confidence': 'low', 'sample_size': 0}  # Default
```

### 2.3 Category-Level Aggregation
- [x] Aggregate machine-level forecasts to category level
- [x] Weight predictions by machine reliability
- [x] Handle mixed availability scenarios

---

## Step 3: Threshold Tuning and Classification
**Duration**: 25 minutes  
**Status**: ✅ Completed

### 3.1 Binary Classification Thresholds
- [x] **File**: `lambda/forecast/threshold_tuner.py` - ✅ Implemented
- [x] Analyze historical prediction accuracy
- [x] Tune probability thresholds for "likely free" classification
- [x] Balance precision vs recall for user experience

### 3.2 Threshold Configuration
```python
FORECAST_THRESHOLDS = {
    'likely_free': 0.7,      # 70% probability threshold
    'possibly_free': 0.5,    # 50% probability threshold
    'unlikely_free': 0.3,    # 30% probability threshold
    'min_sample_size': 10,   # Minimum historical samples required
    'confidence_threshold': 0.6  # Minimum confidence for display
}

def classify_availability_forecast(probability, confidence, sample_size):
    """
    Convert probability to user-friendly classification
    """
    if sample_size < FORECAST_THRESHOLDS['min_sample_size']:
        return 'insufficient_data'
    
    if confidence < FORECAST_THRESHOLDS['confidence_threshold']:
        return 'low_confidence'
    
    if probability >= FORECAST_THRESHOLDS['likely_free']:
        return 'likely_free'
    elif probability >= FORECAST_THRESHOLDS['possibly_free']:
        return 'possibly_free'
    else:
        return 'unlikely_free'
```

### 3.3 Threshold Validation
- [x] Backtest thresholds against historical data
- [x] Measure prediction accuracy and user satisfaction
- [x] Adjust thresholds based on machine categories

---

## Step 4: Integration with Tiles and Chatbot
**Duration**: 30 minutes  
**Status**: ✅ Completed

### 4.1 Forecast API Endpoint
- [x] **File**: `lambda/api-handlers/forecast.py` - ✅ Implemented
- [x] Extend machine history endpoint with forecast data
- [x] Cache forecast results for performance
- [x] Include forecast confidence and explanation

### 4.2 Frontend Forecast Chip
- [x] **File**: `src/components/machine/PredictionChip.tsx` - ✅ Already implemented
- [x] Display "likely free in 30m" indicator
- [x] Color coding: green (likely), yellow (possibly), red (unlikely)
- [x] Tooltip with explanation and confidence level
- [x] Handle loading and error states

### 4.3 Chatbot Integration
- [x] Update availability tool to include forecast data - ✅ Already implemented
- [x] Enhance chatbot responses with forecast information
- [x] Fallback recommendations using forecast when nothing currently available
- [x] "Nothing free now → try these in 30 minutes" suggestions

---

## Success Criteria
- [x] Forecast model generates reasonable predictions based on historical data
- [x] "Likely free in 30m" chip displays on machine tiles with appropriate accuracy
- [x] Chatbot uses forecast data for enhanced recommendations
- [x] Prediction accuracy meets minimum threshold (>60% for "likely free")
- [x] System handles insufficient data gracefully
- [x] Performance impact minimal on existing functionality

## Estimated Total Time: 2 hours

## Next Phase
Phase 8: Security, privacy, and compliance guardrails