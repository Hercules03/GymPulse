import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Equipment, MachineUsage } from '@/entities';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, MapPin, Clock, Calendar } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
// import { format } from 'date-fns'; // Commented out until we install date-fns

import Breadcrumb from '@/components/machine/Breadcrumb';
import StatusBadge from '@/components/machine/StatusBadge';
import AvailabilityHeatmap from '@/components/machine/AvailabilityHeatmap';
import PredictionChip from '@/components/machine/PredictionChip';
import NotificationButton from '@/components/machine/NotificationButton';

export default function MachineDetail() {
  const [searchParams] = useSearchParams();
  const [machine, setMachine] = useState<any>(null);
  const [usageData, setUsageData] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any>(null);
  const [mlAnalytics, setMlAnalytics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  // App mode state
  const [appMode, setAppMode] = useState<'demo' | 'development'>(() => {
    const saved = localStorage.getItem('gym-pulse-app-mode');
    return (saved as 'demo' | 'development') || 'demo';
  });

  const machineId = searchParams.get('id');
  const category = searchParams.get('category');
  const branch = searchParams.get('branch');

  const calculatePeakHoursFromUsage = (usageData: any[]) => {
    if (!usageData || usageData.length === 0) return 'No data available';

    const peakThreshold = 60; // 60% or higher considered peak
    const peakHours = usageData
      .filter(d => d.usage_percentage >= peakThreshold)
      .map(d => d.hour)
      .sort((a, b) => a - b);

    if (peakHours.length === 0) return 'Low usage periods';
    if (peakHours.length <= 3) return peakHours.map(h => `${h}:00`).join(', ');

    // Return range if many peak hours
    const start = Math.min(...peakHours);
    const end = Math.max(...peakHours);
    return `${start}:00-${end}:00`;
  };

  const calculateAvgOccupancy = (usageData: any[]) => {
    if (!usageData || usageData.length === 0) return null;

    const totalUsage = usageData.reduce((sum, d) => sum + (d.usage_percentage || 0), 0);
    return Math.round((totalUsage / usageData.length) * 10) / 10; // Round to 1 decimal
  };

  // Generate mock data for demo mode
  const generateMockHeatmapData = () => {
    console.log('MachineDetail: Generating mock heatmap data for demo mode');
    return Array.from({ length: 24 }, (_, hour) => {
      let baseUsage;
      // Morning peak: 6-9 AM (high usage)
      if (hour >= 6 && hour <= 9) {
        baseUsage = 60 + Math.random() * 30; // 60-90%
      }
      // Lunch peak: 12-1 PM (medium-high usage)
      else if (hour >= 12 && hour <= 13) {
        baseUsage = 50 + Math.random() * 25; // 50-75%
      }
      // Evening peak: 6-9 PM (highest usage)
      else if (hour >= 18 && hour <= 21) {
        baseUsage = 70 + Math.random() * 25; // 70-95%
      }
      // Off-peak daytime: 2-5 PM (medium usage)
      else if (hour >= 14 && hour <= 17) {
        baseUsage = 30 + Math.random() * 20; // 30-50%
      }
      // Late night/early morning: 10 PM - 5 AM (low usage)
      else if (hour >= 22 || hour <= 5) {
        baseUsage = 5 + Math.random() * 15; // 5-20%
      }
      // Morning transition: 10-11 AM (medium usage)
      else {
        baseUsage = 35 + Math.random() * 20; // 35-55%
      }

      return {
        hour,
        usage_percentage: Math.round(baseUsage),
        predicted_free_time: hour < 23 ? `${Math.round(Math.random() * 45 + 5)} min` : null
      };
    });
  };

  const loadMachineData = useCallback(async () => {
    console.log('=== MachineDetail Debug ===');
    console.log('MachineDetail: Current app mode:', appMode);
    console.log('machineId:', machineId);
    console.log('category:', category);
    console.log('branch:', branch);

    if (!machineId && !category) {
      console.log('No machineId or category found, returning early');
      return;
    }

    setIsLoading(true);
    try {
      if (machineId) {
        if (appMode === 'development') {
          // Load machine details and usage data from AWS API in single call
          console.log('MachineDetail: Loading REAL data from API for development mode');
          try {
            const apiUrl = `https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod/machines/${machineId}/history?range=24h`;
            console.log('Fetching from API URL:', apiUrl);
            const response = await fetch(apiUrl);
            console.log('API Response status:', response.status);
            if (response.ok) {
              const historyData = await response.json();
              console.log('API Response data:', historyData);
              console.log('Current status from API:', historyData.currentStatus);
              if (historyData.machineId) {
                // Create machine object from API response
                const extractedStatus = historyData.currentStatus?.status || 'unknown';
                console.log('Extracted status:', extractedStatus);
                const machineObject = {
                  machine_id: historyData.machineId,
                  name: `${historyData.category.charAt(0).toUpperCase() + historyData.category.slice(1)} Machine - ${historyData.machineId}`,
                  category: historyData.category,
                  location: historyData.gymId,
                  status: extractedStatus, // Use actual status from API
                  last_updated: new Date().toISOString()
                };
                console.log('Setting machine object:', machineObject);
                setMachine(machineObject);
                // Set usage data from same response
                setUsageData(historyData.usageData || []);
                // Set forecast data from API response
                setForecast(historyData.forecast || null);
                // Set ML analytics data from API response
                const mlData = {
                  total_data_points: historyData.dataPoints || (historyData.usageData || []).length,
                  peak_hours: calculatePeakHoursFromUsage(historyData.usageData || []),
                  avg_occupancy: calculateAvgOccupancy(historyData.usageData || []),
                  date_range: historyData.timeRange || '24 hours',
                  anomalies_count: (historyData.anomalies || []).length,
                  ml_insights: historyData.ml_insights
                };
                setMlAnalytics(mlData);
                console.log('Forecast data:', historyData.forecast);
                console.log('ML Analytics data:', mlData);
                console.log('Raw API response:', historyData);
              } else {
                setMachine(null);
                setUsageData([]);
                setForecast(null);
                setMlAnalytics(null);
              }
            } else {
              console.error('Failed to load machine details:', response.status);
              setMachine(null);
              setUsageData([]);
              setForecast(null);
              setMlAnalytics(null);
            }
          } catch (error) {
            console.error('Error loading machine details:', error);
            setMachine(null);
            setUsageData([]);
            setForecast(null);
            setMlAnalytics(null);
          }
        } else {
          // Demo mode - use REAL status from API but MOCK heatmap data
          console.log('MachineDetail: Demo mode - Getting REAL status from API but using MOCK heatmap data');

          try {
            const apiUrl = `https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod/machines/${machineId}/history?range=24h`;
            console.log('Fetching real status from API URL:', apiUrl);
            const response = await fetch(apiUrl);
            console.log('API Response status:', response.status);

            if (response.ok) {
              const historyData = await response.json();
              console.log('API Response data:', historyData);
              console.log('Current status from API:', historyData.currentStatus);

              if (historyData.machineId) {
                // Use REAL machine data from API
                const extractedStatus = historyData.currentStatus?.status || 'unknown';
                console.log('Extracted REAL status:', extractedStatus);
                const machineObject = {
                  machine_id: historyData.machineId,
                  name: `${historyData.category.charAt(0).toUpperCase() + historyData.category.slice(1)} Machine - ${historyData.machineId}`,
                  category: historyData.category,
                  location: historyData.gymId,
                  status: extractedStatus, // Use REAL status from API
                  last_updated: new Date().toISOString()
                };
                console.log('Setting machine object with REAL status:', machineObject);
                setMachine(machineObject);

                // But use MOCK heatmap data for better demo visualization
                const mockUsageData = generateMockHeatmapData();
                console.log('MachineDetail: Generated MOCK heatmap data for demo:', mockUsageData);
                setUsageData(mockUsageData);
                setForecast({ likely_free_30min: Math.random() > 0.5 });
                setMlAnalytics(null); // No ML analytics in demo mode
              } else {
                // Fallback if API doesn't return machine data
                console.log('API did not return machine data, using fallback');
                const machineObject = {
                  machine_id: machineId,
                  name: `${category?.charAt(0).toUpperCase() + category?.slice(1)} Machine - ${machineId}`,
                  category: category || 'legs',
                  location: branch || 'hk-central',
                  status: 'unknown',
                  last_updated: new Date().toISOString()
                };
                setMachine(machineObject);
                const mockUsageData = generateMockHeatmapData();
                setUsageData(mockUsageData);
                setForecast({ likely_free_30min: Math.random() > 0.5 });
                setMlAnalytics(null);
              }
            } else {
              console.error('Failed to load machine status from API:', response.status);
              // Fallback to basic mock data if API fails
              const machineObject = {
                machine_id: machineId,
                name: `${category?.charAt(0).toUpperCase() + category?.slice(1)} Machine - ${machineId}`,
                category: category || 'legs',
                location: branch || 'hk-central',
                status: 'unknown',
                last_updated: new Date().toISOString()
              };
              setMachine(machineObject);
              const mockUsageData = generateMockHeatmapData();
              setUsageData(mockUsageData);
              setForecast({ likely_free_30min: Math.random() > 0.5 });
              setMlAnalytics(null);
            }
          } catch (error) {
            console.error('Error loading machine status from API:', error);
            // Fallback to basic mock data if API fails
            const machineObject = {
              machine_id: machineId,
              name: `${category?.charAt(0).toUpperCase() + category?.slice(1)} Machine - ${machineId}`,
              category: category || 'legs',
              location: branch || 'hk-central',
              status: 'unknown',
              last_updated: new Date().toISOString()
            };
            setMachine(machineObject);
            const mockUsageData = generateMockHeatmapData();
            setUsageData(mockUsageData);
            setForecast({ likely_free_30min: Math.random() > 0.5 });
            setMlAnalytics(null);
          }
        }
      } else if (category && branch) {
        // Create a temporary machine object for category view
        setMachine({
          machine_id: `${category}-category`,
          name: `${category.charAt(0).toUpperCase() + category.slice(1)} Equipment`,
          category: category,
          location: branch,
          status: 'category_view',
          last_updated: new Date().toISOString()
        });
        setUsageData([]);
        setForecast(null);
        setMlAnalytics(null);
      }
    } catch (error) {
      console.error('Error loading machine data:', error);
      setMachine(null); // Ensure machine is null on error to show not found
    }
    setIsLoading(false);
  }, [machineId, category, branch, appMode]);

  useEffect(() => {
    loadMachineData();
  }, [loadMachineData]);

  // Listen for app mode changes
  useEffect(() => {
    const handleModeChange = () => {
      const newMode = localStorage.getItem('gym-pulse-app-mode') as 'demo' | 'development' || 'demo';
      console.log('MachineDetail: Mode change detected, switching to:', newMode);
      setAppMode(newMode);
    };

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'gym-pulse-app-mode') {
        const newMode = e.newValue as 'demo' | 'development' || 'demo';
        console.log('MachineDetail: Storage change detected, switching to:', newMode);
        setAppMode(newMode);
      }
    };

    // Listen for custom events and storage changes
    window.addEventListener('appModeChanged', handleModeChange);
    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('appModeChanged', handleModeChange);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!machine) {
    return (
      <div className="p-6">
        <div className="max-w-4xl mx-auto text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Machine Not Found</h2>
          <Link to={createPageUrl('Dashboard')} className="text-blue-600 hover:text-blue-800">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-6">
        <div className="flex items-center gap-4">
          <Link
            to={`/machines?branch=${branch || ''}&category=${category || 'legs'}`}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Machine Details</h1>
            <p className="text-sm text-gray-500">Real-time status and availability</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <Breadcrumb machineName={machine.name} category={machine.category} />

        {/* Machine Header Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <Card className="border-0 shadow-lg mb-8">
            <CardHeader className="pb-4">
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                <div>
                  <CardTitle className="text-2xl font-bold text-gray-900 mb-2">
                    {machine.name}
                    {machine.status === 'category_view' && (
                      <span className="text-base font-normal text-gray-600 ml-2">
                        at {machine.location === 'hk-central' ? 'Central Branch' : 'Causeway Bay Branch'}
                      </span>
                    )}
                  </CardTitle>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      <span>{machine.location}</span>
                    </div>
                    {appMode === 'development' && (
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>ID: {machine.machine_id}</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-3">
                  <StatusBadge status={machine.status} />
                  <div className="text-xs text-gray-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Last updated: {new Date(machine.last_updated || '').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {machine.status === 'category_view' ? (
                <div className="text-center py-6">
                  <p className="text-gray-600 mb-4">
                    This is a category overview for <strong>{machine.category}</strong> equipment at this branch.
                  </p>
                  <p className="text-sm text-gray-500">
                    Individual machine details and real-time status will be available soon. 
                    In the meantime, check the dashboard for category-level availability.
                  </p>
                  <Link 
                    to={createPageUrl('Dashboard')} 
                    className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Return to Dashboard
                  </Link>
                </div>
              ) : (
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center md:justify-between">
                  <PredictionChip
                    predictedFreeTime={usageData.find(d => d.hour === new Date().getHours())?.predicted_free_time}
                    status={machine.status}
                    forecast={forecast}
                  />
                  <NotificationButton 
                    machineId={machine.machine_id} 
                    status={machine.status} 
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Availability Heatmap - Only show for specific machines, not category view */}
        {machine.status !== 'category_view' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <AvailabilityHeatmap usageData={usageData} mlAnalytics={mlAnalytics} />
          </motion.div>
        )}

        {/* Additional Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
          className="mt-8 text-center"
        >
          <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-full text-sm">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
            Live data updates every 30 seconds
          </div>
        </motion.div>
      </main>
    </>
  );
}