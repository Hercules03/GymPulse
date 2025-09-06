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
  const [isLoading, setIsLoading] = useState(true);

  const machineId = searchParams.get('id');

  const loadMachineData = useCallback(async () => {
    if (!machineId) return;
    
    setIsLoading(true);
    try {
      // Load machine details
      const machines = await Equipment.filter({ machine_id: machineId });
      if (machines.length > 0) {
        setMachine(machines[0]);
      } else {
        setMachine(null); // Explicitly set to null if not found
      }

      // Load usage data
      const usage = await MachineUsage.filter({ machine_id: machineId });
      setUsageData(usage);
    } catch (error) {
      console.error('Error loading machine data:', error);
      setMachine(null); // Ensure machine is null on error to show not found
    }
    setIsLoading(false);
  }, [machineId]);

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
              <div className="flex flex-col md:flex-row gap-4 items-start md:items-center md:justify-between">
                <PredictionChip 
                  predictedFreeTime={usageData.find(d => d.hour === new Date().getHours())?.predicted_free_time}
                  status={machine.status}
                />
                <NotificationButton 
                  machineId={machine.machine_id} 
                  status={machine.status} 
                />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Availability Heatmap */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <AvailabilityHeatmap usageData={usageData} />
        </motion.div>

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