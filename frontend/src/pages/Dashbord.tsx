import React, { useState, useEffect, useCallback } from 'react';
import { gymService } from '@/services/gymService';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';

import Header from '@/components/dashboard/Header';
import CategoryCard from '@/components/dashboard/CategoryCard';
import QuickStats from '@/components/dashboard/QuickStats';

export default function Dashboard() {
  const [branches, setBranches] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('hk-central');
  const [isLoading, setIsLoading] = useState(true);

  const locations = [
    { id: 'hk-central', name: 'Central Branch' },
    { id: 'hk-causeway', name: 'Causeway Bay Branch' }
  ];

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
    
    const peakHours = '6-8 PM';
    const maintenanceNeeded = totalEquipment > 0 ? Math.floor(totalEquipment * 0.05) : 1; // Estimate 5% in maintenance

    return { totalEquipment, totalAvailable, peakHours, maintenanceNeeded };
  };

  const getCategoryStats = () => {
    const categories = ['legs', 'chest', 'back'];
    return categories.map(category => {
      // Calculate totals for SELECTED branch only
      let totalMachines = 0;
      let availableCount = 0;
      
      const selectedBranch = branches.find(branch => branch.id === selectedLocation);
      if (selectedBranch) {
        const categoryData = selectedBranch.categories?.[category];
        if (categoryData) {
          totalMachines = categoryData.total || 0;
          availableCount = categoryData.free || 0;
        }
      }
      
      const occupiedCount = totalMachines - availableCount;
      const offlineCount = 0; // Will be calculated when we have machine-level data

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
          <div className="inline-flex items-center gap-2 bg-green-50 text-green-700 px-4 py-2 rounded-full text-sm">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </motion.div>
      </main>
    </div>
  );
}