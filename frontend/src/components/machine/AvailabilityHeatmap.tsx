import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface UsageData {
  hour: number;
  usage_percentage: number;
  timestamp: string;
  predicted_free_time?: number | null;
}

interface AvailabilityHeatmapProps {
  usageData: UsageData[];
  mlAnalytics?: {
    peak_hours?: string;
    avg_occupancy?: number;
    total_data_points?: number;
    date_range?: string;
    anomalies_count?: number;
    ml_insights?: string;
    forecast_summary?: any;
  };
}

export default function AvailabilityHeatmap({ usageData, mlAnalytics }: AvailabilityHeatmapProps) {
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const currentHour = new Date().getHours();

  const getIntensityColor = (usage: number) => {
    const intensity = Math.round(usage); // usage is already percentage 0-100
    if (intensity >= 80) return 'bg-red-500';
    if (intensity >= 60) return 'bg-orange-500';
    if (intensity >= 40) return 'bg-yellow-500';
    if (intensity >= 20) return 'bg-green-500';
    return 'bg-green-200';
  };

  const getUsageForHour = (hour: number) => {
    const data = usageData.find(d => d.hour === hour);
    return data ? data.usage_percentage : 0;
  };

  return (
    <Card className="border-0 shadow-lg">
      <CardHeader>
        <CardTitle className="text-xl font-bold text-gray-900">
          Today's Usage Pattern
        </CardTitle>
        <p className="text-sm text-gray-500">
          Usage intensity throughout the day (darker = busier)
        </p>
      </CardHeader>
      <CardContent>
        {/* Legend */}
        <div className="flex items-center justify-between mb-6 text-xs text-gray-500">
          <span>Less busy</span>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-200 rounded"></div>
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <div className="w-3 h-3 bg-orange-500 rounded"></div>
            <div className="w-3 h-3 bg-red-500 rounded"></div>
          </div>
          <span>More busy</span>
        </div>

        {/* Heatmap Grid */}
        <div className="grid grid-cols-12 gap-2 mb-4">
          {hours.map(hour => {
            const usage = getUsageForHour(hour);
            const isCurrentHour = hour === currentHour;
            const intensity = Math.round(usage); // usage is already percentage 0-100
            
            return (
              <div key={hour} className="text-center">
                <div
                  className={`w-full h-8 rounded ${getIntensityColor(usage)} ${
                    isCurrentHour ? 'ring-2 ring-blue-500 ring-offset-1' : ''
                  } transition-all duration-200 hover:scale-110 cursor-pointer relative group`}
                  title={`${hour}:00 - ${intensity}% busy`}
                >
                  {isCurrentHour && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-white"></div>
                  )}
                  
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                    {hour}:00 - {intensity}% busy
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {hour.toString().padStart(2, '0')}
                </div>
              </div>
            );
          })}
        </div>

        {/* Time labels */}
        <div className="grid grid-cols-4 gap-4 text-xs text-gray-500 mt-4">
          <div className="text-center">6 AM</div>
          <div className="text-center">12 PM</div>
          <div className="text-center">6 PM</div>
          <div className="text-center">12 AM</div>
        </div>

        {/* Current status */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-900">Current Time</p>
              <p className="text-xs text-blue-700">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-blue-900">
                {Math.round(getUsageForHour(currentHour))}% busy
              </p>
              <p className="text-xs text-blue-700">
                {getUsageForHour(currentHour) < 30 ? 'Low usage' :
                 getUsageForHour(currentHour) < 70 ? 'Moderate usage' : 'High usage'}
              </p>
            </div>
          </div>
        </div>

        {/* AI Insights Section */}
        {usageData.length > 0 && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 text-sm font-semibold">🧠</span>
                </div>
              </div>
              <div className="flex-grow min-w-0">
                <h4 className="text-sm font-medium text-blue-900 mb-2">🧠 ML Analytics</h4>
                <div className="space-y-2 text-sm">
                  <div className="text-blue-800">
                    🔮 <strong>Data Analysis:</strong> {mlAnalytics?.total_data_points || usageData.length} historical data points
                    {mlAnalytics?.date_range && (
                      <span className="text-blue-600 ml-1">({mlAnalytics.date_range})</span>
                    )}
                  </div>
                  <div className="text-blue-700">
                    📈 <strong>Peak Hours:</strong> {
                      mlAnalytics?.peak_hours ||
                      (() => {
                        const peakHours = usageData
                          .filter(d => d.usage_percentage > 70)
                          .map(d => `${d.hour}:00`)
                          .slice(0, 3);
                        return peakHours.length > 0 ? peakHours.join(', ') : 'Low usage periods';
                      })()
                    }
                  </div>
                  <div className="text-blue-700">
                    ⚡ <strong>Avg Occupancy:</strong> {
                      mlAnalytics?.avg_occupancy ?
                        `${mlAnalytics.avg_occupancy}% (Real analysis)` :
                        'Calculating...'
                    }
                  </div>
                  {mlAnalytics?.anomalies_count !== undefined && (
                    <div className="text-blue-600 text-xs">
                      🔍 <strong>Anomalies Detected:</strong> {mlAnalytics.anomalies_count} unusual patterns
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}