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
  const [machine, setMachine] = useState(null);
  const [usageData, setUsageData] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const machineId = searchParams.get('id');
  const category = searchParams.get('category');
  const branch = searchParams.get('branch');

  const loadMachineData = useCallback(async () => {
    console.log('=== MachineDetail Debug ===');
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
        // Load machine details and usage data from AWS API in single call
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
              console.log('Forecast data:', historyData.forecast);
            } else {
              setMachine(null);
              setUsageData([]);
              setForecast(null);
            }
          } else {
            console.error('Failed to load machine details:', response.status);
            setMachine(null);
            setUsageData([]);
            setForecast(null);
          }
        } catch (error) {
          console.error('Error loading machine details:', error);
          setMachine(null);
          setUsageData([]);
          setForecast(null);
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
      }
    } catch (error) {
      console.error('Error loading machine data:', error);
      setMachine(null); // Ensure machine is null on error to show not found
    }
    setIsLoading(false);
  }, [machineId, category, branch]);

  useEffect(() => {
    loadMachineData();
  }, [loadMachineData]);

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
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <Link 
            to={createPageUrl('Dashboard')} 
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
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>ID: {machine.machine_id}</span>
                    </div>
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
            <AvailabilityHeatmap usageData={usageData} />
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