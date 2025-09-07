import React from 'react';
import { Clock, TrendingUp, TrendingDown, AlertCircle, Info } from 'lucide-react';

interface ForecastData {
  classification?: string;
  display_text?: string;
  color?: string;
  confidence?: string;
  confidence_text?: string;
  show_to_user?: boolean;
  likelyFreeIn30m?: boolean;
  metadata?: {
    probability?: number;
    sample_size?: number;
    reliable?: boolean;
  };
}

interface PredictionChipProps {
  predictedFreeTime?: string;
  status: 'available' | 'occupied' | 'offline';
  forecast?: ForecastData;
}

export default function PredictionChip({ predictedFreeTime, status, forecast }: PredictionChipProps) {
  // Handle machine currently available
  if (status === 'available') {
    if (forecast?.show_to_user && forecast?.classification) {
      // Show forecast for how long it might stay free
      const bgColor = forecast.color === 'green' ? 'bg-green-50 text-green-700' : 
                     forecast.color === 'yellow' ? 'bg-yellow-50 text-yellow-700' :
                     forecast.color === 'red' ? 'bg-red-50 text-red-700' : 
                     'bg-blue-50 text-blue-700';
      
      return (
        <div className={`inline-flex items-center gap-2 px-3 py-2 ${bgColor} rounded-lg text-sm`}>
          <Clock className="w-4 h-4" />
          <span>Free now</span>
          {forecast.metadata?.reliable && (
            <div className="flex items-center gap-1 text-xs opacity-75">
              <Info className="w-3 h-3" />
              <span>{forecast.confidence} confidence</span>
            </div>
          )}
        </div>
      );
    }
    
    return (
      <div className="inline-flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg text-sm">
        <Clock className="w-4 h-4" />
        <span>Ready to use</span>
      </div>
    );
  }

  // Handle offline machines
  if (status === 'offline') {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg text-sm">
        <AlertCircle className="w-4 h-4" />
        <span>Currently offline</span>
      </div>
    );
  }

  // Handle occupied machines with forecast
  if (status === 'occupied') {
    // Use enhanced forecast if available
    if (forecast?.show_to_user && forecast?.display_text) {
      const bgColor = forecast.color === 'green' ? 'bg-green-50 text-green-700' : 
                     forecast.color === 'yellow' ? 'bg-yellow-50 text-yellow-700' :
                     forecast.color === 'red' ? 'bg-red-50 text-red-700' : 
                     'bg-gray-50 text-gray-700';
      
      const Icon = forecast.classification === 'likely_free' ? TrendingUp :
                  forecast.classification === 'unlikely_free' ? TrendingDown :
                  Clock;

      return (
        <div className={`inline-flex items-center gap-2 px-3 py-2 ${bgColor} rounded-lg text-sm`}>
          <Icon className="w-4 h-4" />
          <span>{forecast.display_text}</span>
          {forecast.metadata?.reliable && forecast.confidence !== 'none' && (
            <div className="flex items-center gap-1 text-xs opacity-75">
              <Info className="w-3 h-3" />
              <span>{forecast.confidence}</span>
            </div>
          )}
        </div>
      );
    }
    
    // Fallback to legacy predicted time format
    if (predictedFreeTime) {
      return (
        <div className="inline-flex items-center gap-2 px-3 py-2 bg-orange-50 text-orange-700 rounded-lg text-sm">
          <Clock className="w-4 h-4" />
          <span>Available in ~{predictedFreeTime}</span>
        </div>
      );
    }

    // Default occupied state
    return (
      <div className="inline-flex items-center gap-2 px-3 py-2 bg-orange-50 text-orange-700 rounded-lg text-sm">
        <Clock className="w-4 h-4" />
        <span>Currently in use</span>
      </div>
    );
  }

  // Default fallback
  return (
    <div className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg text-sm">
      <Clock className="w-4 h-4" />
      <span>Status unknown</span>
    </div>
  );
}