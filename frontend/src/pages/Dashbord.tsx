import React, { useState, useEffect, useCallback } from 'react';
import { Equipment } from '@/entities/Equipment';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';

import Header from '@/components/dashboard/Header';
import CategoryCard from '@/components/dashboard/CategoryCard';
import QuickStats from '@/components/dashboard/QuickStats';

export default function Dashboard() {
  const [equipment, setEquipment] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('Downtown');
  const [isLoading, setIsLoading] = useState(true);

  const locations = ['Downtown', 'Westside', 'North Campus', 'Eastside'];

  const loadEquipment = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await Equipment.filter({ location: selectedLocation });
      setEquipment(data);
    } catch (error) {
      console.error('Error loading equipment:', error);
    }
    setIsLoading(false);
  }, [selectedLocation]);

  useEffect(() => {
    loadEquipment();
  }, [loadEquipment]);

  const getStats = () => {
    const totalEquipment = equipment.length;
    const totalAvailable = equipment.filter(eq => eq.status === 'available').length;
    const peakHours = '6-8 PM';
    const maintenanceNeeded = equipment.filter(eq => eq.status === 'offline').length;

    return { totalEquipment, totalAvailable, peakHours, maintenanceNeeded };
  };

  const getCategoryStats = () => {
    const categories = ['legs', 'chest', 'back'];
    return categories.map(category => {
      const categoryEquipment = equipment.filter(eq => eq.category === category);
      const totalMachines = categoryEquipment.length;
      const availableCount = categoryEquipment.filter(eq => eq.status === 'available').length;
      const occupiedCount = categoryEquipment.filter(eq => eq.status === 'occupied').length;
      const offlineCount = categoryEquipment.filter(eq => eq.status === 'offline').length;

      return {
        category,
        totalMachines,
        availableCount,
        occupiedCount,
        offlineCount,
        machines: categoryEquipment.map(m => ({ 
            name: m.name, 
            status: m.status, 
            machine_id: m.machine_id 
        }))
      };
    });
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
                  to={createPageUrl(`MachineDetail?id=${categoryData.machines.find(m => m.status === 'available')?.machine_id || categoryData.machines[0]?.machine_id || ''}`)}
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