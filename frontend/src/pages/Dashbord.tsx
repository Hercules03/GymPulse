import React, { useState, useEffect, useCallback } from 'react';
import { gymService } from '@/services/gymService';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { useMachineUpdates } from '@/hooks/useWebSocket';

import Header from '@/components/dashboard/Header';
import CategoryCard from '@/components/dashboard/CategoryCard';
import QuickStats from '@/components/dashboard/QuickStats';

export default function Dashboard() {
  const [branches, setBranches] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('hk-central');
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date());

  const locations = [
    { id: 'hk-central', name: 'Central Branch' },
    { id: 'hk-causeway', name: 'Causeway Bay Branch' }
  ];

  // WebSocket integration for real-time updates
  const webSocket = useMachineUpdates({
    branches: ['hk-central', 'hk-causeway'], // Subscribe to both branches
    categories: ['legs', 'chest', 'back']
  });

  const loadBranches = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await gymService.getBranches();
      setBranches(response.branches || []);
      console.log('Loaded branches from AWS API:', response.branches);
    } catch (error) {
      console.error('Error loading branches from AWS:', error);
      // Keep empty array, don't fall back to mock data
      setBranches([]);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    loadBranches();
  }, [loadBranches]);

  // Update last update time when WebSocket receives new data
  useEffect(() => {
    if (webSocket.lastUpdate) {
      setLastUpdateTime(new Date());
      console.log('🔄 Dashboard received WebSocket update:', webSocket.lastUpdate);
    }
  }, [webSocket.lastUpdate]);

  // Update WebSocket subscriptions when location changes
  useEffect(() => {
    if (webSocket.updateSubscriptions) {
      webSocket.updateSubscriptions({
        branches: ['hk-central', 'hk-causeway'], // Always subscribe to both branches for dashboard
        categories: ['legs', 'chest', 'back']
      });
    }
  }, [selectedLocation, webSocket.updateSubscriptions]);

  const getStats = () => {
    // Calculate totals from real AWS branch data
    let totalEquipment = 0;
    let totalAvailable = 0;
    
    branches.forEach(branch => {
      Object.values(branch.categories || {}).forEach(category => {
        totalEquipment += category.total || 0;
        totalAvailable += category.free || 0;
      });
    });

    // Only update availability with real-time WebSocket data if available
    // Keep totalEquipment constant (from static branch configuration)
    if (webSocket.latestMachineStatus && Object.keys(webSocket.latestMachineStatus).length > 0) {
      const allMachines = Object.values(webSocket.latestMachineStatus);
      // Only update available count if we have meaningful real-time data
      if (allMachines.length > 0) {
        totalAvailable = allMachines.filter(m => m.status === 'free').length;
      }
    }
    
    const peakHours = '6-8 PM';
    const maintenanceNeeded = totalEquipment > 0 ? Math.floor(totalEquipment * 0.05) : 1; // Estimate 5% in maintenance

    return { totalEquipment, totalAvailable, peakHours, maintenanceNeeded };
  };

  const getCategoryStats = () => {
    const categories = ['legs', 'chest', 'back'];
    return categories.map(category => {
      // Start with base counts from static branch data
      let totalMachines = 0;
      let baseAvailableCount = 0;
      
      const selectedBranch = branches.find(branch => branch.id === selectedLocation);
      if (selectedBranch) {
        const categoryData = selectedBranch.categories?.[category];
        if (categoryData) {
          totalMachines = categoryData.total || 0;
          baseAvailableCount = categoryData.free || 0;
        }
      }

      // Override with real-time WebSocket data if available
      let availableCount = baseAvailableCount;
      let occupiedCount = totalMachines - baseAvailableCount;
      let offlineCount = 0;

      if (webSocket.latestMachineStatus && Object.keys(webSocket.latestMachineStatus).length > 0) {
        // Count real-time status for machines in this category and location
        const categoryMachines = Object.values(webSocket.latestMachineStatus).filter(
          machine => machine.category === category && machine.gymId === selectedLocation
        );

        if (categoryMachines.length > 0) {
          // Update only availability counts based on real-time data
          // Keep totalMachines constant (from static branch configuration)
          availableCount = categoryMachines.filter(m => m.status === 'free').length;
          occupiedCount = categoryMachines.filter(m => m.status === 'occupied').length;
          offlineCount = categoryMachines.filter(m => m.status === 'offline').length;
          
          // Note: totalMachines should remain constant from branch configuration
          // Real-time data only tells us about machines that recently updated
        }
      }

      return {
        category,
        totalMachines,
        availableCount,
        occupiedCount,
        offlineCount,
        machines: [] // Will be populated when we have machine-level data
      };
    });
  };

  const getSampleMachineId = (category) => {
    // Map categories to actual machine IDs based on simulator configuration
    const machineMapping = {
      'legs': selectedLocation === 'hk-central' ? 'leg-press-01' : 'leg-press-03',
      'chest': selectedLocation === 'hk-central' ? 'bench-press-01' : 'bench-press-03', 
      'back': selectedLocation === 'hk-central' ? 'lat-pulldown-01' : 'lat-pulldown-02'
    };
    return machineMapping[category] || 'leg-press-01';
  };

  const stats = getStats();
  const categoryStats = getCategoryStats();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        selectedLocation={selectedLocation}
        onLocationChange={setSelectedLocation}
        locations={locations}
      />

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Quick Stats */}
        <QuickStats {...stats} />

        {/* Main Categories Grid */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Equipment Categories</h2>
              <p className="text-gray-500 text-sm">Real-time availability by category</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="text-gray-600">Available</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500"></div>
                <span className="text-gray-600">Occupied</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gray-400"></div>
                <span className="text-gray-600">Offline</span>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map(i => (
                <div key={i} className="animate-pulse">
                  <div className="bg-white rounded-lg p-6 shadow-sm h-full">
                    <div className="flex items-center justify-between mb-6">
                      <div className="w-12 h-12 bg-gray-200 rounded-xl"></div>
                      <div className="text-right">
                        <div className="w-8 h-8 bg-gray-200 rounded"></div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="w-3/4 h-4 bg-gray-200 rounded"></div>
                      <div className="w-1/2 h-3 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {categoryStats.map((categoryData, index) => (
                 <Link 
                  key={categoryData.category}
                  to={createPageUrl(`machines?branch=${selectedLocation}&category=${categoryData.category}`)}
                 >
                    <motion.div
                      className="h-full"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: index * 0.1 }}
                    >
                      <CategoryCard {...categoryData} />
                    </motion.div>
                 </Link>
              ))}
            </div>
          )}
        </div>

        {/* Live Status */}
        <motion.div 
          className="text-center py-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm ${
            webSocket.isConnected 
              ? 'bg-green-50 text-green-700' 
              : webSocket.isConnecting 
                ? 'bg-yellow-50 text-yellow-700' 
                : 'bg-red-50 text-red-700'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              webSocket.isConnected 
                ? 'bg-green-500 animate-pulse' 
                : webSocket.isConnecting 
                  ? 'bg-yellow-500 animate-pulse' 
                  : 'bg-red-500'
            }`}></div>
            {webSocket.isConnected 
              ? `Live updates • Last: ${lastUpdateTime.toLocaleTimeString()}`
              : webSocket.isConnecting 
                ? 'Connecting to live updates...'
                : 'Offline - Manual refresh needed'
            }
          </div>
        </motion.div>
      </main>
    </div>
  );
}